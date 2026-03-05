"""Pilot Queue Plugin - ZippyQ-style self-service queue for RotorHazard."""

import logging
from flask import jsonify, request, templating
from flask.blueprints import Blueprint
from eventmanager import Evt

from .queue_manager import QueueManager

logger = logging.getLogger(__name__)

# Global queue manager instance
qm = QueueManager()


def initialize(rhapi):
    qm.load()
    logger.info("[PilotQueue] Plugin initialized")

    bp = Blueprint(
        'pilot_queue',
        __name__,
        template_folder='pages',
        static_folder='static',
        static_url_path='/pilot_queue/static'
    )

    # ============================================
    # PAGES
    # ============================================

    @bp.route('/pilot_queue/')
    def kiosk_page():
        return templating.render_template(
            'queue_kiosk.html',
            serverInfo=None,
            getOption=rhapi.db.option,
            __=rhapi.__
        )

    @bp.route('/pilot_queue/admin')
    def admin_page():
        return templating.render_template(
            'queue_admin.html',
            serverInfo=None,
            getOption=rhapi.db.option,
            __=rhapi.__
        )

    # ============================================
    # API: STATUS
    # ============================================

    @bp.route('/pilot_queue/api/status', methods=['GET'])
    def api_status():
        """Get full queue state with pilot eligibility."""
        status = qm.get_status(rhapi)
        return jsonify(status)

    # ============================================
    # API: JOIN / LEAVE
    # ============================================

    @bp.route('/pilot_queue/api/join', methods=['POST'])
    def api_join():
        """Pilot joins a slot queue. Body: {pilot_id: int, slot: int}"""
        data = request.get_json()
        if not data or 'pilot_id' not in data or 'slot' not in data:
            return jsonify({'success': False, 'message': 'Missing pilot_id or slot'}), 400

        pilot_id = int(data['pilot_id'])
        slot = int(data['slot'])

        success, message = qm.join(pilot_id, slot)

        # Auto-generate if enabled and ready
        heat_id = None
        if success and qm.config.get('auto_generate') and qm.can_generate_heat():
            gen_success, gen_msg, heat_id = qm.generate_heat(rhapi)
            if gen_success:
                message += f". {gen_msg}"

        return jsonify({'success': success, 'message': message, 'heat_id': heat_id})

    @bp.route('/pilot_queue/api/leave', methods=['POST'])
    def api_leave():
        """Pilot leaves a slot queue. Body: {pilot_id: int, slot: int}"""
        data = request.get_json()
        if not data or 'pilot_id' not in data or 'slot' not in data:
            return jsonify({'success': False, 'message': 'Missing pilot_id or slot'}), 400

        pilot_id = int(data['pilot_id'])
        slot = int(data['slot'])

        success, message = qm.leave(pilot_id, slot)
        return jsonify({'success': success, 'message': message})

    @bp.route('/pilot_queue/api/replace', methods=['POST'])
    def api_replace():
        """Admin: replace a pilot in a slot. Body: {old_pilot_id: int, new_pilot_id: int, slot: int}"""
        data = request.get_json()
        if not data or 'old_pilot_id' not in data or 'new_pilot_id' not in data or 'slot' not in data:
            return jsonify({'success': False, 'message': 'Missing old_pilot_id, new_pilot_id, or slot'}), 400

        old_pilot_id = int(data['old_pilot_id'])
        new_pilot_id = int(data['new_pilot_id'])
        slot = int(data['slot'])

        success, message = qm.replace(old_pilot_id, new_pilot_id, slot)
        return jsonify({'success': success, 'message': message})

    @bp.route('/pilot_queue/api/replace_in_heat', methods=['POST'])
    def api_replace_in_heat():
        """Admin: replace a pilot in a generated heat. Body: {heat_id: int, old_pilot_id: int, new_pilot_id: int}"""
        data = request.get_json()
        if not data or 'heat_id' not in data or 'old_pilot_id' not in data or 'new_pilot_id' not in data:
            return jsonify({'success': False, 'message': 'Missing heat_id, old_pilot_id, or new_pilot_id'}), 400

        heat_id = int(data['heat_id'])
        old_pilot_id = int(data['old_pilot_id'])
        new_pilot_id = int(data['new_pilot_id'])

        success, message = qm.replace_in_heat(heat_id, old_pilot_id, new_pilot_id, rhapi)
        return jsonify({'success': success, 'message': message})

    # ============================================
    # API: HEATS INFO
    # ============================================

    @bp.route('/pilot_queue/api/heats', methods=['GET'])
    def api_heats():
        """Get details of all generated heats with pilots and results."""
        heats = qm.get_heats_info(rhapi)
        return jsonify({'heats': heats})

    # ============================================
    # API: HEAT GENERATION
    # ============================================

    @bp.route('/pilot_queue/api/generate', methods=['POST'])
    def api_generate():
        """Admin: manually generate next heat from queue."""
        success, message, heat_id = qm.generate_heat(rhapi)
        return jsonify({'success': success, 'message': message, 'heat_id': heat_id})

    # ============================================
    # API: CONFIG
    # ============================================

    @bp.route('/pilot_queue/api/config', methods=['GET'])
    def api_get_config():
        """Get queue configuration."""
        # Include available classes for the admin dropdown
        classes = []
        try:
            for rc in rhapi.db.raceclasses:
                classes.append({'id': rc.id, 'name': rc.name or f'Class {rc.id}'})
        except Exception as e:
            logger.error(f"[PilotQueue] Error loading classes: {e}")

        return jsonify({
            'config': qm.config,
            'classes': classes
        })

    @bp.route('/pilot_queue/api/config', methods=['POST'])
    def api_update_config():
        """Update queue configuration. Body: config object."""
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        # Type coercion for numeric fields
        if 'class_id' in data and data['class_id'] is not None:
            data['class_id'] = int(data['class_id'])
        if 'max_packs' in data:
            data['max_packs'] = int(data['max_packs'])
        if 'max_queue' in data:
            data['max_queue'] = int(data['max_queue'])
        if 'rest_rounds' in data:
            data['rest_rounds'] = int(data['rest_rounds'])
        if 'num_slots' in data:
            data['num_slots'] = int(data['num_slots'])
        if 'auto_generate' in data:
            data['auto_generate'] = bool(data['auto_generate'])

        qm.update_config(data)
        return jsonify({'success': True, 'config': qm.config})

    # ============================================
    # API: RESET
    # ============================================

    @bp.route('/pilot_queue/api/reset', methods=['POST'])
    def api_reset():
        """Clear all queues and pilot stats."""
        qm.reset()
        return jsonify({'success': True, 'message': 'Queue reset'})

    # ============================================
    # EVENT HOOKS
    # ============================================

    def on_laps_save(args):
        """Called when race laps are saved. Update pack counts."""
        try:
            heat_id = rhapi.race.heat
            if heat_id:
                qm.on_race_saved(heat_id, rhapi)
        except Exception as e:
            logger.error(f"[PilotQueue] Error in on_laps_save: {e}")

    rhapi.events.on(Evt.LAPS_SAVE, on_laps_save)

    # ============================================
    # REGISTER
    # ============================================

    rhapi.ui.blueprint_add(bp)
