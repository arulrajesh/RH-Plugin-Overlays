"""Pilot Queue Manager - Core queue logic and persistence."""

import os
import json
import logging
import threading

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
STATE_FILE = os.path.join(DATA_DIR, 'queue_state.json')

DEFAULT_CONFIG = {
    'class_id': None,
    'max_packs': 10,
    'max_queue': 2,
    'rest_rounds': 0,
    'auto_generate': True,
    'num_slots': 4
}


class QueueManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.config = dict(DEFAULT_CONFIG)
        self.slots = [[] for _ in range(self.config['num_slots'])]
        self.pilot_stats = {}  # {str(pilot_id): {packs_flown, packs_queued, last_heat_num}}
        self.heat_counter = 0
        self.generated_heats = []

    def load(self):
        """Load state from JSON file."""
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                self.config = {**DEFAULT_CONFIG, **data.get('config', {})}
                self.slots = data.get('slots', [[] for _ in range(self.config['num_slots'])])
                self.pilot_stats = data.get('pilot_stats', {})
                self.heat_counter = data.get('heat_counter', 0)
                heats = data.get('generated_heats', [])
                self.generated_heats = []
                for h in heats:
                    if isinstance(h, int):
                        self.generated_heats.append({
                            'heat_id': h, 'heat_name': 'Q Heat (legacy)',
                            'heat_num': 0, 'slot_pilots': {}, 'completed': True
                        })
                    else:
                        self.generated_heats.append(h)
                # Ensure correct number of slots
                while len(self.slots) < self.config['num_slots']:
                    self.slots.append([])
                while len(self.slots) > self.config['num_slots']:
                    self.slots.pop()
                logger.info(f"[PilotQueue] Loaded state: {self.heat_counter} heats, {sum(len(s) for s in self.slots)} queued")
            except Exception as e:
                logger.error(f"[PilotQueue] Failed to load state: {e}")

    def save(self):
        """Save state to JSON file."""
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            data = {
                'config': self.config,
                'slots': self.slots,
                'pilot_stats': self.pilot_stats,
                'heat_counter': self.heat_counter,
                'generated_heats': self.generated_heats
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[PilotQueue] Failed to save state: {e}")

    def get_pilot_stat(self, pilot_id):
        """Get or create pilot stats entry."""
        key = str(pilot_id)
        if key not in self.pilot_stats:
            self.pilot_stats[key] = {
                'packs_flown': 0,
                'packs_queued': 0,
                'last_heat_num': -999  # Never raced
            }
        return self.pilot_stats[key]

    def can_join(self, pilot_id):
        """Check if a pilot is eligible to join the queue.
        Returns (eligible: bool, reason: str)
        """
        stat = self.get_pilot_stat(pilot_id)

        # Check max packs
        total = stat['packs_flown'] + stat['packs_queued']
        if total >= self.config['max_packs']:
            return False, f"Pack limit reached ({stat['packs_flown']}/{self.config['max_packs']} flown)"

        # Check max queue entries
        if stat['packs_queued'] >= self.config['max_queue']:
            return False, f"Already queued {stat['packs_queued']} time(s)"

        # Check rest period (only applies after a race is completed)
        if stat['last_heat_num'] >= 0:
            rounds_since = self.heat_counter - stat['last_heat_num']
            if rounds_since < self.config['rest_rounds']:
                remaining = self.config['rest_rounds'] - rounds_since
                return False, f"Resting ({remaining} heat(s) remaining)"

        return True, "Eligible"

    def join(self, pilot_id, slot):
        """Add a pilot to a slot queue.
        Returns (success: bool, message: str)
        """
        with self._lock:
            # Validate slot
            if slot < 0 or slot >= self.config['num_slots']:
                return False, "Invalid slot"

            # Check eligibility
            eligible, reason = self.can_join(pilot_id)
            if not eligible:
                return False, reason

            # The pilot will be placed at this row index in the queue grid
            target_row = len(self.slots[slot])

            # A pilot cannot be in two different slots in the same round
            for other_slot in range(self.config['num_slots']):
                if other_slot == slot:
                    continue
                if target_row < len(self.slots[other_slot]) and self.slots[other_slot][target_row] == pilot_id:
                    return False, "Already in another slot for that round"

            # Add to queue
            self.slots[slot].append(pilot_id)
            stat = self.get_pilot_stat(pilot_id)
            stat['packs_queued'] += 1

            self.save()
            logger.info(f"[PilotQueue] Pilot {pilot_id} joined slot {slot}")
            return True, "Joined queue"

    def leave(self, pilot_id, slot):
        """Remove a pilot from a slot queue.
        Returns (success: bool, message: str)
        """
        with self._lock:
            if slot < 0 or slot >= self.config['num_slots']:
                return False, "Invalid slot"

            if pilot_id not in self.slots[slot]:
                return False, "Not in this slot's queue"

            self.slots[slot].remove(pilot_id)
            stat = self.get_pilot_stat(pilot_id)
            stat['packs_queued'] = max(0, stat['packs_queued'] - 1)

            self.save()
            logger.info(f"[PilotQueue] Pilot {pilot_id} left slot {slot}")
            return True, "Left queue"

    def replace(self, old_pilot_id, new_pilot_id, slot):
        """Replace a pilot in a slot queue with another pilot.
        The new pilot must not already be in the same round (row index) in another slot.
        Returns (success: bool, message: str)
        """
        with self._lock:
            if slot < 0 or slot >= self.config['num_slots']:
                return False, "Invalid slot"

            if old_pilot_id not in self.slots[slot]:
                return False, "Original pilot not in this slot's queue"

            # Find the row index of the old pilot in this slot
            row_idx = self.slots[slot].index(old_pilot_id)

            # Check new pilot is not in the same round in another slot
            for other_slot in range(self.config['num_slots']):
                if other_slot == slot:
                    continue
                if row_idx < len(self.slots[other_slot]) and self.slots[other_slot][row_idx] == new_pilot_id:
                    return False, "New pilot already in another slot for that round"

            # Do the replacement
            self.slots[slot][row_idx] = new_pilot_id

            # Update stats: decrement old, increment new
            old_stat = self.get_pilot_stat(old_pilot_id)
            old_stat['packs_queued'] = max(0, old_stat['packs_queued'] - 1)
            new_stat = self.get_pilot_stat(new_pilot_id)
            new_stat['packs_queued'] += 1

            self.save()
            logger.info(f"[PilotQueue] Replaced pilot {old_pilot_id} with {new_pilot_id} in slot {slot} row {row_idx}")
            return True, "Pilot replaced"

    def replace_in_heat(self, heat_id, old_pilot_id, new_pilot_id, rhapi):
        """Replace a pilot in a generated (non-completed) heat.
        Updates both our tracking and the actual RotorHazard heat.
        Returns (success: bool, message: str)
        """
        with self._lock:
            # Find the heat entry
            heat_entry = None
            for h in self.generated_heats:
                if isinstance(h, dict) and h.get('heat_id') == heat_id:
                    heat_entry = h
                    break

            if heat_entry is None:
                return False, "Heat not found"

            if heat_entry.get('completed'):
                return False, "Cannot modify a completed heat"

            # Find which slot the old pilot is in
            slot_pilots = heat_entry.get('slot_pilots', {})
            old_slot_idx = None
            for idx, pid in slot_pilots.items():
                if pid == old_pilot_id:
                    old_slot_idx = idx
                    break

            if old_slot_idx is None:
                return False, "Pilot not found in this heat"

            # Check new pilot is not already in this heat
            for idx, pid in slot_pilots.items():
                if pid == new_pilot_id:
                    return False, "New pilot already in this heat"

            # Update our tracking
            heat_entry['slot_pilots'][old_slot_idx] = new_pilot_id

            # Update the actual RotorHazard heat slot
            try:
                rh_slots = rhapi.db.slots_by_heat(heat_id)
                slot_index = int(old_slot_idx)
                if slot_index < len(rh_slots):
                    rhapi.db.slot_alter(rh_slots[slot_index].id, pilot=new_pilot_id)
            except Exception as e:
                # Rollback our tracking
                heat_entry['slot_pilots'][old_slot_idx] = old_pilot_id
                logger.error(f"[PilotQueue] Failed to alter RH slot: {e}")
                return False, f"Failed to update heat: {str(e)}"

            # Update pilot stats
            old_stat = self.get_pilot_stat(old_pilot_id)
            old_stat['packs_queued'] = max(0, old_stat['packs_queued'] - 1)
            new_stat = self.get_pilot_stat(new_pilot_id)
            new_stat['packs_queued'] += 1

            # Broadcast changes to RotorHazard frontend
            try:
                rhapi.ui.broadcast_heats()
            except Exception as e:
                logger.warning(f"[PilotQueue] Could not broadcast heats: {e}")

            self.save()
            logger.info(f"[PilotQueue] Replaced pilot {old_pilot_id} with {new_pilot_id} in heat {heat_id} slot {old_slot_idx}")
            return True, "Pilot replaced in heat"

    def _set_next_heat(self, rhapi):
        """Set RotorHazard's current heat to the oldest uncompleted generated heat (FIFO)."""
        for h in self.generated_heats:
            if isinstance(h, dict) and not h.get('completed'):
                try:
                    rhapi.race.heat = h['heat_id']
                    logger.info(f"[PilotQueue] Set current heat to {h['heat_id']} ({h.get('heat_name', '')})")
                except Exception as e:
                    logger.warning(f"[PilotQueue] Could not set current heat: {e}")
                return

    def can_generate_heat(self):
        """Check if we can generate a heat (all slots have at least 1 pilot)."""
        for i in range(self.config['num_slots']):
            if len(self.slots[i]) == 0:
                return False
        return True

    def generate_heat(self, rhapi):
        """Pop the first pilot from each slot and create a heat in RotorHazard.
        Returns (success: bool, message: str, heat_id: int or None)
        """
        with self._lock:
            if not self.config.get('class_id'):
                return False, "No race class configured", None

            if not self.can_generate_heat():
                return False, "Not all slots have a pilot queued", None

            # Pop first pilot from each slot
            pilots = []
            for i in range(self.config['num_slots']):
                pilot_id = self.slots[i].pop(0)
                pilots.append(pilot_id)

            # Create heat in RotorHazard
            try:
                self.heat_counter += 1
                heat_name = f"Q Heat {self.heat_counter}"
                heat = rhapi.db.heat_add(name=heat_name, raceclass=self.config['class_id'])

                # Assign pilots to slots
                rh_slots = rhapi.db.slots_by_heat(heat.id)
                for i, pilot_id in enumerate(pilots):
                    if i < len(rh_slots):
                        rhapi.db.slot_alter(rh_slots[i].id, pilot=pilot_id)

                heat_entry = {
                    'heat_id': heat.id,
                    'heat_name': heat_name,
                    'heat_num': self.heat_counter,
                    'slot_pilots': {},
                    'completed': False
                }
                for i, pilot_id in enumerate(pilots):
                    heat_entry['slot_pilots'][str(i)] = pilot_id
                self.generated_heats.append(heat_entry)

                # Broadcast to RotorHazard frontend so heat dropdown updates
                try:
                    rhapi.ui.broadcast_heats()
                except Exception as e:
                    logger.warning(f"[PilotQueue] Could not broadcast heats: {e}")

                # Set current heat to oldest uncompleted (FIFO)
                self._set_next_heat(rhapi)

                self.save()

                pilot_names = []
                for pid in pilots:
                    try:
                        p = rhapi.db.pilot_by_id(pid)
                        pilot_names.append(p.callsign if p else str(pid))
                    except:
                        pilot_names.append(str(pid))

                logger.info(f"[PilotQueue] Generated {heat_name}: {', '.join(pilot_names)}")
                return True, f"Created {heat_name}", heat.id

            except Exception as e:
                # Rollback: put pilots back at front of their slots
                for i, pilot_id in enumerate(pilots):
                    self.slots[i].insert(0, pilot_id)
                self.heat_counter -= 1
                self.save()
                logger.error(f"[PilotQueue] Failed to generate heat: {e}")
                return False, f"Failed to create heat: {str(e)}", None

    def on_race_saved(self, heat_id, rhapi):
        """Called when a race is saved. Update pack counts for pilots in that heat."""
        heat_entry = None
        for h in self.generated_heats:
            if isinstance(h, dict) and h.get('heat_id') == heat_id:
                heat_entry = h
                break

        if heat_entry is None:
            return  # Not one of our heats

        with self._lock:
            heat_entry['completed'] = True
            try:
                heat_num = heat_entry.get('heat_num', self.heat_counter)
                rh_slots = rhapi.db.slots_by_heat(heat_id)
                for slot in rh_slots:
                    if slot.pilot_id:
                        stat = self.get_pilot_stat(slot.pilot_id)
                        stat['packs_flown'] += 1
                        stat['packs_queued'] = max(0, stat['packs_queued'] - 1)
                        stat['last_heat_num'] = heat_num

                self.save()
                logger.info(f"[PilotQueue] Updated pack counts for heat {heat_id}")

            except Exception as e:
                logger.error(f"[PilotQueue] Failed to update stats for heat {heat_id}: {e}")

        # Auto-generate next heat if enabled
        if self.config.get('auto_generate') and self.can_generate_heat():
            success, msg, new_heat_id = self.generate_heat(rhapi)
            if success:
                logger.info(f"[PilotQueue] Auto-generated next heat: {msg}")

        # Advance to the oldest uncompleted heat (FIFO)
        self._set_next_heat(rhapi)

    def get_status(self, rhapi=None):
        """Get full queue status for API response."""
        status = {
            'config': self.config,
            'slots': self.slots,
            'heat_counter': self.heat_counter,
            'can_generate': self.can_generate_heat(),
            'pilot_stats': {},
            'slot_counts': [len(s) for s in self.slots]
        }

        # Build pilot eligibility info
        if rhapi:
            try:
                all_pilots = rhapi.db.pilots
                for pilot in all_pilots:
                    pid = pilot.id
                    stat = self.get_pilot_stat(pid)
                    eligible, reason = self.can_join(pid)

                    # Count how many slots this pilot is in
                    in_slots = []
                    for si in range(self.config['num_slots']):
                        if pid in self.slots[si]:
                            in_slots.append(si)

                    status['pilot_stats'][str(pid)] = {
                        'callsign': pilot.callsign,
                        'packs_flown': stat['packs_flown'],
                        'packs_queued': stat['packs_queued'],
                        'last_heat_num': stat['last_heat_num'],
                        'eligible': eligible,
                        'reason': reason,
                        'in_slots': in_slots
                    }
            except Exception as e:
                logger.error(f"[PilotQueue] Error building status: {e}")

        return status

    def get_heats_info(self, rhapi=None):
        """Get detailed info about all generated heats for the kiosk display."""
        heats = []
        current_heat_id = None
        try:
            current_heat_id = rhapi.race.heat if rhapi else None
        except:
            pass

        for entry in self.generated_heats:
            heat_id = entry.get('heat_id')
            completed = entry.get('completed', False)

            # Determine status
            if completed:
                status = 'completed'
            elif heat_id == current_heat_id:
                status = 'active'
            else:
                status = 'upcoming'

            # Resolve pilot names
            pilots = []
            slot_pilots = entry.get('slot_pilots', {})
            for slot_idx in sorted(slot_pilots.keys(), key=int):
                pid = slot_pilots[slot_idx]
                callsign = str(pid)
                packs = 0
                if rhapi:
                    try:
                        p = rhapi.db.pilot_by_id(pid)
                        if p:
                            callsign = p.callsign or str(pid)
                    except:
                        pass
                stat = self.get_pilot_stat(pid)
                packs = stat['packs_flown'] + stat['packs_queued']
                pilots.append({
                    'slot': int(slot_idx),
                    'pilot_id': pid,
                    'callsign': callsign,
                    'packs': packs
                })

            heat_info = {
                'heat_id': heat_id,
                'heat_name': entry.get('heat_name', ''),
                'heat_num': entry.get('heat_num', 0),
                'pilots': pilots,
                'status': status
            }

            # For completed heats, try to get results
            if completed and rhapi:
                try:
                    results = rhapi.db.heat_results(heat_id)
                    if results and hasattr(results, 'get'):
                        lb = results.get('by_consecutives') or results.get('by_race_time') or []
                        result_list = []
                        for r in lb:
                            result_list.append({
                                'position': r.get('position', ''),
                                'callsign': r.get('callsign', ''),
                                'laps': r.get('laps', 0),
                                'total_time': r.get('total_time', ''),
                                'fastest_lap': r.get('fastest_lap', '')
                            })
                        heat_info['results'] = result_list
                except:
                    pass

            heats.append(heat_info)

        return heats

    def update_config(self, new_config):
        """Update configuration. Adjusts slot count if changed."""
        with self._lock:
            old_num_slots = self.config.get('num_slots', 4)
            self.config.update(new_config)

            new_num_slots = self.config.get('num_slots', 4)
            if new_num_slots != old_num_slots:
                while len(self.slots) < new_num_slots:
                    self.slots.append([])
                while len(self.slots) > new_num_slots:
                    removed = self.slots.pop()
                    # Decrement packs_queued for removed pilots
                    for pid in removed:
                        stat = self.get_pilot_stat(pid)
                        stat['packs_queued'] = max(0, stat['packs_queued'] - 1)

            self.save()

    def reset(self):
        """Clear all queues and stats."""
        with self._lock:
            self.slots = [[] for _ in range(self.config['num_slots'])]
            self.pilot_stats = {}
            self.heat_counter = 0
            self.generated_heats = []
            self.save()
            logger.info("[PilotQueue] Queue reset")
