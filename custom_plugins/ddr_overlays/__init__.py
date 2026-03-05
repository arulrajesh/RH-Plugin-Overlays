'''DDR Overlays Plugin'''

import os
import json
import logging
import requests
import zipfile

from RHUI import UIField, UIFieldType, UIFieldSelectOption

from flask import jsonify, request, templating
from flask.blueprints import Blueprint

logger = logging.getLogger(__name__)

# Read the JSON file
with open('plugins/ddr_overlays/static/data/countries.json', 'r') as file:
    countries_data = json.load(file)
options = []
for country in countries_data:
    code = country["alpha2"]
    name = country["name"]
    option = UIFieldSelectOption(code, name)
    options.append(option)
options.sort(key=lambda x: x.label)
country_ui_field = UIField('country', "Country Code", UIFieldType.SELECT, options=options, value="")

# Folder for pilot images
PILOT_IMAGE_UPLOAD_FOLDER = 'shared/avatars'
os.makedirs(PILOT_IMAGE_UPLOAD_FOLDER, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def initialize(rhapi):
    rhapi.fields.register_pilot_attribute( country_ui_field )

    bp = Blueprint(
        'ddr_overlays',
        __name__,
        template_folder='pages',
        static_folder='static',
        static_url_path='/ddr_overlays/static'
    )

    ### home page ###
    @bp.route('/ddr_overlays')
    def ddr_overlays_homePage():
        return templating.render_template('ddr_overlay_index.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__)

    ### API tester page ###
    @bp.route('/ddr_overlays/api-tester')
    def ddr_overlays_apiTester():
        return templating.render_template('api_tester.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__)

    ### Spectator display ###
    @bp.route('/ddr_overlays/spectator-display')
    def ddr_overlays_spectatorDisplay():
        return templating.render_template('spectator_display.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__)

    ### live results ###
    @bp.route('/ddr_overlays/stream/results')
    def ddr_overlays_streamResults():
        return templating.render_template('stream/results.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__, DEBUG=False)

    ### bar ###
    @bp.route('/ddr_overlays/stream/bar')
    def ddr_overlays_streamBar():
        return templating.render_template('stream/bar.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__, DEBUG=False)

    ### overlays based on bracket type and class ###
    @bp.route('/ddr_overlays/stream/leaderboard/<string:bracket_type>/<int:class_id>')
    def ddr_overlays_streamLeaderboard(bracket_type, class_id):
        return templating.render_template('stream/leaderboard.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__, DEBUG=False,
            bracket_type=bracket_type, class_id=class_id
        )

    @bp.route('/ddr_overlays/stream/leaderboard_pages/<string:bracket_type>/<int:class_id>')
    def ddr_overlays_streamLeaderboardPages(bracket_type, class_id):
        return templating.render_template('stream/leaderboard_pages.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__, DEBUG=False,
            bracket_type=bracket_type, class_id=class_id
        )

    @bp.route('/ddr_overlays/stream/brackets/<string:bracket_type>/<int:class_id>')
    def ddr_overlays_streamBrackets(bracket_type, class_id):
        return templating.render_template('stream/brackets.html', serverInfo=None, getOption=rhapi.db.option,__=rhapi.__, DEBUG=False,
            bracket_type=bracket_type, class_id=class_id
        )

    @bp.route('/ddr_overlays/stream/last_heat/<string:bracket_type>/<int:class_id>')
    def ddr_overlays_streamLastHeat(bracket_type, class_id):
        return templating.render_template('stream/last_heat.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__, DEBUG=False,
            bracket_type=bracket_type, class_id=class_id
        )

    @bp.route('/ddr_overlays/stream/next_up/<string:bracket_type>/<int:class_id>')
    def ddr_overlays_streamNextUp(bracket_type, class_id):
        return templating.render_template('stream/next_up.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__, DEBUG=False,
            bracket_type=bracket_type, class_id=class_id, num_nodes=8
        )

    @bp.route('/ddr_overlays/stream/podium/<string:bracket_type>/<int:class_id>')
    def ddr_overlays_streamPodium(bracket_type, class_id):
        return templating.render_template('stream/podium.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__, DEBUG=False,
            bracket_type=bracket_type, class_id=class_id
        )

    ### DE leaderboard ###
    @bp.route('/ddr_overlays/stream/de_leaderboard/<int:seeding_class_id>/<int:de_class_id>')
    def ddr_overlays_streamDELeaderboard(seeding_class_id, de_class_id):
        return templating.render_template('stream/de_leaderboard.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__, DEBUG=False,
            seeding_class_id=seeding_class_id, de_class_id=de_class_id, portrait=False
        )

    @bp.route('/ddr_overlays/stream/de_leaderboard/<int:seeding_class_id>/<int:de_class_id>/portrait')
    def ddr_overlays_streamDELeaderboardPortrait(seeding_class_id, de_class_id):
        return templating.render_template('stream/de_leaderboard.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__, DEBUG=False,
            seeding_class_id=seeding_class_id, de_class_id=de_class_id, portrait=True
        )
    ### DE Bracket visual overlay ###
    @bp.route('/ddr_overlays/stream/de_bracket/<int:seeding_class_id>/<int:de_class_id>')
    def ddr_overlays_streamDEBracket(seeding_class_id, de_class_id):
        return templating.render_template('stream/de_bracket.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__, DEBUG=False,
            seeding_class_id=seeding_class_id, de_class_id=de_class_id
        )
    ################################################

    ### node ###
    @bp.route('/ddr_overlays/stream/node/<int:node_id>')
    def ddr_overlays_streamNode(node_id):
        if node_id <= 8:
            return templating.render_template('stream/node.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__, DEBUG=False,
                node_id=node_id-1
            )
        else:
            return False

    ################################################

    ### upload pilot image ###
    @bp.route("/upload_pilot_image", methods=["POST"])
    def upload_pilot_image():
        if "file" not in request.files:
            return jsonify({"error": "no file"}), 400

        file = request.files["file"]
        pilot_id = request.form.get("pilot_id", "unknown")

        if file.filename == "":
            return jsonify({"error": "empty filename"}), 400

        if not allowed_image(file.filename):
            return jsonify({"error": "invalid extension"}), 400

        # size check
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > 10 * 1024 * 1024:
            return jsonify({"error": "file too big (more than 10 MB)"}), 400

        filename = file.filename
        filepath = os.path.join(PILOT_IMAGE_UPLOAD_FOLDER, filename)
        file.seek(0)
        file.save(filepath)

        # public URL to get the image
        file_url = filepath

        return jsonify({"success": True, "new_url": file_url})

    ### API endpoints for settings (server-side storage) ###
    SETTINGS_FILE = 'plugins/ddr_overlays/data/settings.json'
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)

    def load_settings():
        """Load settings from JSON file"""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_settings(settings):
        """Save settings to JSON file"""
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    @bp.route("/ddr_overlays/api/settings", methods=["GET"])
    def get_settings():
        """Get all settings"""
        settings = load_settings()
        return jsonify(settings)

    @bp.route("/ddr_overlays/api/settings", methods=["POST"])
    def update_settings():
        """Update settings"""
        try:
            new_settings = request.get_json()
            if not new_settings:
                return jsonify({"error": "No data provided"}), 400

            settings = load_settings()
            settings.update(new_settings)

            if save_settings(settings):
                return jsonify({"success": True, "settings": settings})
            else:
                return jsonify({"error": "Failed to save settings"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    ### API Testing / Data Endpoints ###

    @bp.route("/ddr_overlays/api/node/<int:node_id>/data", methods=["GET"])
    def get_node_data(node_id):
        """Get complete data for a specific node including pilot, position, colors, etc."""
        try:
            # Get current heat
            heat = rhapi.db.heat_by_id(rhapi.race.heat)
            if not heat:
                return jsonify({"error": "No active heat"}), 404

            # Get pilot assigned to this node
            pilot_id = None
            for slot in heat.slots:
                if slot.node_index == node_id:
                    pilot_id = slot.pilot_id
                    break

            if not pilot_id:
                return jsonify({"error": f"No pilot assigned to node {node_id}"}), 404

            # Get pilot data
            pilot = rhapi.db.pilot_by_id(pilot_id)

            # Get leaderboard for position
            results = rhapi.race.results
            position = None
            lap_data = []

            if results and 'by_race_time' in results:
                for idx, entry in enumerate(results['by_race_time']):
                    if entry.get('pilot_id') == pilot_id:
                        position = idx + 1
                        lap_data = entry.get('laps', [])
                        break

            # Get active color
            active_color = None
            color_mode = rhapi.db.option('colorMode', default='pilot')

            if color_mode == 'pilot':
                active_color = pilot.color if pilot else None
            else:
                # Node-based color
                active_color = rhapi.db.option(f'nodeColor_{node_id}')

            return jsonify({
                "node_id": node_id,
                "pilot": {
                    "id": pilot.id if pilot else None,
                    "callsign": pilot.callsign if pilot else None,
                    "name": pilot.name if pilot else None,
                    "team": pilot.team if pilot else None,
                    "color": pilot.color if pilot else None,
                    "phonetic": pilot.phonetic if pilot else None,
                    "active_color": active_color
                },
                "position": position,
                "lap_data": lap_data,
                "avatar_url": f"/shared/avatars/{pilot.callsign.lower().replace(' ', '_')}.jpg" if pilot else None,
                "flag_url": f"/ddr_overlays/static/imgs/flags/{getattr(pilot, 'country', 'unknown')}.jpg" if pilot else None
            })
        except Exception as e:
            logger.error(f"Error getting node data: {e}")
            return jsonify({"error": str(e)}), 500

    @bp.route("/ddr_overlays/api/pilot/<int:pilot_id>/avatar", methods=["GET"])
    def get_pilot_avatar_url(pilot_id):
        """Get avatar URL for a specific pilot"""
        try:
            pilot = rhapi.db.pilot_by_id(pilot_id)
            if not pilot:
                return jsonify({"error": "Pilot not found"}), 404

            avatar_url = f"/shared/avatars/{pilot.callsign.lower().replace(' ', '_')}.jpg"
            return jsonify({
                "pilot_id": pilot_id,
                "callsign": pilot.callsign,
                "avatar_url": avatar_url,
                "full_url": request.host_url.rstrip('/') + avatar_url
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @bp.route("/ddr_overlays/api/pilot/<int:pilot_id>/position", methods=["GET"])
    def get_pilot_position(pilot_id):
        """Get current race position for a pilot"""
        try:
            results = rhapi.race.results
            if not results or 'by_race_time' not in results:
                return jsonify({"error": "No race results available"}), 404

            for idx, entry in enumerate(results['by_race_time']):
                if entry.get('pilot_id') == pilot_id:
                    return jsonify({
                        "pilot_id": pilot_id,
                        "position": idx + 1,
                        "total_positions": len(results['by_race_time']),
                        "laps": entry.get('laps_count', 0),
                        "total_time": entry.get('total_time_raw', 0),
                        "fastest_lap": entry.get('fastest_lap_raw', 0)
                    })

            return jsonify({"error": "Pilot not in current race"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @bp.route("/ddr_overlays/api/pilot/<int:pilot_id>/color", methods=["GET"])
    def get_pilot_color(pilot_id):
        """Get active color for a pilot (respects seat/pilot color mode)"""
        try:
            pilot = rhapi.db.pilot_by_id(pilot_id)
            if not pilot:
                return jsonify({"error": "Pilot not found"}), 404

            # Find which node this pilot is on
            heat = rhapi.db.heat_by_id(rhapi.race.heat)
            node_id = None
            if heat:
                for slot in heat.slots:
                    if slot.pilot_id == pilot_id:
                        node_id = slot.node_index
                        break

            # Get color based on mode
            color_mode = rhapi.db.option('colorMode', default='pilot')

            if color_mode == 'pilot':
                active_color = pilot.color
                color_source = 'pilot'
            else:
                # Node-based color
                active_color = rhapi.db.option(f'nodeColor_{node_id}') if node_id is not None else pilot.color
                color_source = 'node' if node_id is not None else 'pilot_fallback'

            # Get secondary color from plugin settings
            settings = load_settings()
            secondary_colors = settings.get('pilot_secondary_colors', {})
            secondary_color = secondary_colors.get(str(pilot_id))

            return jsonify({
                "pilot_id": pilot_id,
                "callsign": pilot.callsign,
                "primary_color": active_color,
                "secondary_color": secondary_color,
                "color_mode": color_mode,
                "color_source": color_source,
                "node_id": node_id
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @bp.route("/ddr_overlays/api/heat/current", methods=["GET"])
    def get_current_heat():
        """Get current heat data with all pilots and their node assignments"""
        try:
            heat = rhapi.db.heat_by_id(rhapi.race.heat)
            if not heat:
                return jsonify({"error": "No active heat"}), 404

            pilots_data = []
            for slot in heat.slots:
                if slot.pilot_id:
                    pilot = rhapi.db.pilot_by_id(slot.pilot_id)
                    if pilot:
                        pilots_data.append({
                            "node_id": slot.node_index,
                            "pilot_id": pilot.id,
                            "callsign": pilot.callsign,
                            "color": pilot.color,
                            "team": pilot.team
                        })

            return jsonify({
                "heat_id": heat.id,
                "heat_name": heat.displayname,
                "class_id": heat.class_id,
                "pilots": pilots_data
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @bp.route("/ddr_overlays/api/leaderboard", methods=["GET"])
    def get_leaderboard():
        """Get current race leaderboard"""
        try:
            results = rhapi.race.results
            if not results or 'by_race_time' not in results:
                return jsonify({"error": "No race results available"}), 404

            leaderboard = []
            for idx, entry in enumerate(results['by_race_time']):
                leaderboard.append({
                    "position": idx + 1,
                    "pilot_id": entry.get('pilot_id'),
                    "callsign": entry.get('callsign'),
                    "laps": entry.get('laps_count', 0),
                    "total_time": entry.get('total_time', ''),
                    "fastest_lap": entry.get('fastest_lap', ''),
                    "average_lap": entry.get('average_lap', ''),
                    "node": entry.get('node')
                })

            return jsonify({
                "leaderboard": leaderboard,
                "heat_id": rhapi.race.heat,
                "race_status": rhapi.race.status
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @bp.route("/ddr_overlays/api_tester")
    def api_tester_page():
        """API testing webapp"""
        return templating.render_template('api_tester.html', serverInfo=None, getOption=rhapi.db.option, __=rhapi.__)

    ### upload pilot image bulk ###
    @bp.route("/upload_zip", methods=["POST"])
    def upload_zip():
        if "zipfile" not in request.files:
            return jsonify({"error": "no file"}), 400

        zip_file = request.files["zipfile"]

        if zip_file.filename == "":
            return jsonify({"error": "empty filename"}), 400

        # size check
        zip_file.seek(0, os.SEEK_END)
        size = zip_file.tell()
        zip_file.seek(0)
        if size > 100 * 1024 * 1024:
            return jsonify({"error": "ZIP file too big (more than 100 MB)"}), 400

        # temporary path
        temp_path = os.path.join(PILOT_IMAGE_UPLOAD_FOLDER, "temp_upload.zip")
        zip_file.save(temp_path)

        # extraction
        try:
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    # avoid path traversal such as "../../"
                    if not os.path.basename(member) == member:
                        os.remove(temp_path)
                        return jsonify({"error": "ZIP file contains subfolders or invalid paths"}), 400

                # extract only valid files
                zip_ref.extractall(PILOT_IMAGE_UPLOAD_FOLDER)
        except zipfile.BadZipFile:
            os.remove(temp_path)
            return jsonify({"error": "file is not a valid ZIP"}), 400

        # remove the temporary archive
        os.remove(temp_path)

        return jsonify({"success": True, "message": "ZIP uploaded successfully"})

    rhapi.ui.blueprint_add(bp)

    rhapi.ui.register_panel("ddr_overlays", "DDR - OBS Overlays", "settings")
    rhapi.ui.register_markdown("ddr_overlays", "DDR Overlays link", "Overlays are available [here](/ddr_overlays)")
