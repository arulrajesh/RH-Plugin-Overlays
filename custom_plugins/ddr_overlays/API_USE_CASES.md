# RotorHazard API Creative Use Cases

## Overview

This document provides creative and practical use cases for the RotorHazard API, demonstrating how to leverage the Socket.IO events and HTTP endpoints to build innovative applications for FPV racing events.

## Access the Testing Webapp

Visit: `http://your-server:5000/ddr_overlays/api-tester`

The interactive API Testing Hub allows you to:
- Test Socket.IO events in real-time
- View live API responses
- Explore creative implementation examples
- Copy code snippets for your own projects

---

## 1. Live Streaming & Broadcasting

### 1.1 Dynamic OBS Overlay with Real-time Updates

**Use Case**: Create professional racing broadcasts with live-updating overlays showing pilot positions, lap times, and race status.

**Key APIs**:
```javascript
// Connect to RotorHazard server
const socket = io('http://your-rotorhazard-server:5000');

// Listen for lap completion
socket.on('laps', (data) => {
    console.log('New lap data:', data);
    updateLapCounter(data.pilot_id, data.lap_number);
    updateLapTime(data.pilot_id, data.lap_time);
});

// Listen for race status changes
socket.on('race_status', (data) => {
    // data.status: 'staging', 'racing', 'done'
    updateRaceStatusBanner(data.status);
});

// Listen for leaderboard updates
socket.on('leaderboard', (data) => {
    updatePilotPositions(data);
});
```

**Expected Output**:
```json
{
  "laps": [
    {
      "pilot_id": 1,
      "pilot_name": "SkyRacer",
      "lap_number": 3,
      "lap_time": 28.456,
      "total_time": 87.234,
      "position": 1
    }
  ],
  "race_status": "racing",
  "leaderboard": [
    {
      "position": 1,
      "callsign": "SkyRacer",
      "laps": 5,
      "total_time": "2:15.234",
      "fastest_lap": "26.12"
    }
  ]
}
```

**Implementation Tips**:
- Use OBS Browser Source pointing to your custom HTML overlay
- Apply CSS animations for smooth transitions
- Show pilot colors from database for visual identification
- Add sound effects on lap completion

---

### 1.2 Multi-Node Split-Screen Display

**Use Case**: Display 4-8 pilot video feeds with individual overlays showing their current stats.

**Endpoint Pattern**:
```javascript
// Individual node overlays
GET /ddr_overlays/stream/node/1  // Pilot in slot 1
GET /ddr_overlays/stream/node/2  // Pilot in slot 2
// ... up to node 8

// Listen for crossing events
socket.on('pass_record', (data) => {
    if (data.node === currentNode) {
        // Flash crossing indicator
        flashCrossingAnimation();
        // Update lap time
        displayNewLapTime(data.lap_time);
    }
});
```

**Creative Enhancement**: Add a "ghost" lap time comparison showing how the pilot is performing vs. their fastest lap.

---

## 2. Race Analytics & Intelligence

### 2.1 Performance Analytics Dashboard

**Use Case**: Build a comprehensive dashboard showing pilot statistics, improvement trends, and head-to-head comparisons.

**API Integration**:
```javascript
// Export complete race data
socket.emit('export_database', {
    'format': 'json'
});

socket.on('database_export', (data) => {
    const races = data.races;
    const pilots = data.pilots;

    // Calculate advanced statistics
    const pilotStats = analyzePilotPerformance(races, pilots);
});

// Analysis functions
function analyzePilotPerformance(races, pilots) {
    return pilots.map(pilot => {
        const pilotRaces = races.filter(r =>
            r.participants.includes(pilot.id)
        );

        const lapTimes = pilotRaces.flatMap(r =>
            r.laps.filter(lap => lap.pilot_id === pilot.id)
                  .map(lap => lap.lap_time)
        );

        return {
            pilot_id: pilot.id,
            callsign: pilot.callsign,
            avg_lap_time: average(lapTimes),
            fastest_lap: Math.min(...lapTimes),
            consistency: standardDeviation(lapTimes),
            races_participated: pilotRaces.length,
            podium_finishes: countPodiums(pilot.id, races),
            improvement_rate: calculateImprovement(lapTimes)
        };
    });
}
```

**Output Structure**:
```json
{
  "pilot_id": 1,
  "callsign": "SkyRacer",
  "avg_lap_time": 28.45,
  "fastest_lap": 26.12,
  "consistency": 0.92,
  "races_participated": 15,
  "podium_finishes": 8,
  "improvement_rate": 0.15,
  "percentile_rank": 85
}
```

**Visualization Ideas**:
- Lap time distribution histogram
- Position change Sankey diagram
- Consistency heat map over time
- Head-to-head matchup win rates

---

### 2.2 Predictive Race Outcomes

**Use Case**: Use ML/statistical analysis on historical data to predict race winners and create pre-race excitement.

**Implementation**:
```javascript
function predictRaceOutcome(heatPilots, historicalData) {
    const predictions = heatPilots.map(pilot => {
        // Get pilot's historical performance
        const pilotHistory = historicalData.filter(
            race => race.pilot_id === pilot.id
        );

        // Calculate factors
        const avgLapTime = calculateAverage(
            pilotHistory.map(r => r.avg_lap_time)
        );
        const consistency = calculateConsistency(pilotHistory);
        const recentForm = getRecentForm(pilotHistory, 5); // Last 5 races
        const trackPerformance = getTrackSpecificPerformance(
            pilot,
            currentTrack
        );

        // Simple prediction algorithm
        const baseScore = 100 / avgLapTime;
        const consistencyBonus = consistency * 10;
        const formBonus = recentForm * 5;
        const trackBonus = trackPerformance * 8;

        const totalScore = baseScore + consistencyBonus +
                          formBonus + trackBonus;

        return {
            pilot_id: pilot.id,
            callsign: pilot.callsign,
            prediction_score: totalScore,
            win_probability: null  // Calculate after all scores
        };
    });

    // Convert scores to probabilities
    const totalScore = predictions.reduce(
        (sum, p) => sum + p.prediction_score, 0
    );

    predictions.forEach(pred => {
        pred.win_probability = pred.prediction_score / totalScore;
    });

    // Sort by probability
    predictions.sort((a, b) =>
        b.win_probability - a.win_probability
    );

    return predictions;
}
```

**Display Format**:
```json
{
  "heat_id": 5,
  "predictions": [
    {
      "callsign": "SkyRacer",
      "win_probability": 0.42,
      "predicted_finish": 1,
      "confidence": "high"
    },
    {
      "callsign": "PropWash",
      "win_probability": 0.31,
      "predicted_finish": 2,
      "confidence": "medium"
    }
  ],
  "upset_potential": 0.15
}
```

---

## 3. Race Automation & Management

### 3.1 Automated Tournament Bracket System

**Use Case**: Automatically progress through tournament brackets without manual intervention.

**Full Automation Flow**:
```javascript
class TournamentAutomation {
    constructor(tournamentType = 'double_elimination') {
        this.tournamentType = tournamentType;
        this.bracket = this.initializeBracket();
        this.setupListeners();
    }

    setupListeners() {
        socket.on('race_save', (data) => {
            this.handleRaceCompletion(data);
        });
    }

    handleRaceCompletion(raceData) {
        const results = raceData.results;

        // Update bracket with results
        this.updateBracketPositions(results);

        // Determine next matchup
        const nextHeat = this.generateNextHeat();

        if (nextHeat) {
            // Create heat in RotorHazard
            this.createHeat(nextHeat);

            // Schedule with break time
            this.scheduleRace(nextHeat.id, 120); // 2-min break

            // Notify participants
            this.notifyPilots(nextHeat.pilots);
        } else {
            // Tournament complete
            this.declareTournamentWinner();
        }
    }

    createHeat(heatConfig) {
        // Create the heat
        socket.emit('add_heat', {
            'note': `${heatConfig.bracket_name} - ${heatConfig.round}`,
            'class': heatConfig.class_id
        });

        socket.on('heat_add', (data) => {
            const heatId = data.heat_id;

            // Assign pilots to slots
            heatConfig.pilots.forEach((pilot, slotIndex) => {
                socket.emit('alter_heat', {
                    'heat': heatId,
                    'slot': slotIndex,
                    'pilot': pilot.id
                });
            });

            heatConfig.id = heatId;
        });
    }

    scheduleRace(heatId, delaySeconds) {
        socket.emit('schedule_race', {
            'heat': heatId,
            'delay_seconds': delaySeconds
        });
    }

    generateNextHeat() {
        // Double elimination logic
        if (this.tournamentType === 'double_elimination') {
            return this.generateDoubleElimHeat();
        }
        // Single elimination logic
        else if (this.tournamentType === 'single_elimination') {
            return this.generateSingleElimHeat();
        }
    }
}

// Initialize tournament
const tournament = new TournamentAutomation('double_elimination');
```

**Benefits**:
- Zero manual heat creation
- Consistent break times
- Automatic pilot notification
- Real-time bracket updates
- Error-free tournament progression

---

### 3.2 Smart Frequency Management

**Use Case**: Automatically assign optimal video frequencies based on pilot equipment and avoid conflicts.

**Implementation**:
```javascript
class FrequencyManager {
    constructor() {
        this.raceband = [5658, 5695, 5732, 5769, 5806, 5843, 5880, 5917];
        this.frequencyMap = new Map();
    }

    assignOptimalFrequencies(heat) {
        const pilots = heat.pilots;
        const assignments = [];

        pilots.forEach((pilot, slotIndex) => {
            // Get pilot's preferred frequency
            const preferred = pilot.preferred_frequency;

            // Check for conflicts
            let assignedFreq = preferred;

            if (this.hasConflict(assignedFreq, slotIndex, assignments)) {
                // Find next available frequency
                assignedFreq = this.findNextAvailable(
                    slotIndex,
                    assignments
                );
            }

            // Assign to node
            socket.emit('set_frequency', {
                'node': slotIndex,
                'frequency': assignedFreq
            });

            assignments.push({
                slot: slotIndex,
                pilot: pilot.callsign,
                frequency: assignedFreq,
                band: this.getBandFromFreq(assignedFreq),
                channel: this.getChannelFromFreq(assignedFreq)
            });

            this.frequencyMap.set(slotIndex, assignedFreq);
        });

        return assignments;
    }

    hasConflict(frequency, slot, assignments) {
        // Check for frequency conflicts (harmonics, etc.)
        return assignments.some(a =>
            Math.abs(a.frequency - frequency) < 40 // 40 MHz separation
        );
    }

    findNextAvailable(slot, assignments) {
        for (let freq of this.raceband) {
            if (!this.hasConflict(freq, slot, assignments)) {
                return freq;
            }
        }
        return this.raceband[slot]; // Fallback
    }
}

// Usage
socket.on('heat_change', (data) => {
    const freqManager = new FrequencyManager();
    const assignments = freqManager.assignOptimalFrequencies(data.heat);
    console.log('Frequency assignments:', assignments);
});
```

---

## 4. System Integration

### 4.1 Discord Bot Integration

**Use Case**: Manage race events and engage community directly through Discord.

**Bot Commands**:
```javascript
const { Client, Intents } = require('discord.js');
const io = require('socket.io-client');

const discordBot = new Client({
    intents: [Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES]
});
const socket = io('http://rotorhazard-server:5000');

// Command: /register
discordBot.on('interactionCreate', async interaction => {
    if (interaction.commandName === 'register') {
        const callsign = interaction.options.getString('callsign');
        const team = interaction.options.getString('team');

        // Register pilot in RotorHazard
        socket.emit('add_pilot', {
            'callsign': callsign,
            'team': team,
            'phonetic': callsign
        });

        socket.once('pilot_add', (data) => {
            interaction.reply(
                `✅ Successfully registered ${callsign}! ` +
                `Your pilot ID is: ${data.pilot_id}`
            );
        });
    }

    // Command: /results
    if (interaction.commandName === 'results') {
        const heatNumber = interaction.options.getInteger('heat');

        // Fetch results (you'd implement this endpoint)
        const results = await fetchHeatResults(heatNumber);

        const embed = {
            color: 0x667eea,
            title: `🏁 Heat ${heatNumber} Results`,
            fields: results.map((r, i) => ({
                name: `${i+1}. ${r.callsign}`,
                value: `Laps: ${r.laps} | Time: ${r.total_time}`,
                inline: false
            })),
            timestamp: new Date()
        };

        interaction.reply({ embeds: [embed] });
    }

    // Command: /schedule
    if (interaction.commandName === 'schedule') {
        // Return upcoming heats
        const schedule = await getUpcomingHeats();

        let scheduleText = '📅 **Upcoming Heats**\n\n';
        schedule.forEach(heat => {
            scheduleText += `**${heat.name}** - ${heat.time}\n`;
            scheduleText += `Pilots: ${heat.pilots.join(', ')}\n\n`;
        });

        interaction.reply(scheduleText);
    }
});

// Auto-announce race results
socket.on('race_save', (data) => {
    const winner = data.results[0];
    const channel = discordBot.channels.cache.get(RACE_CHANNEL_ID);

    channel.send(
        `🏆 **Race Complete!**\n\n` +
        `Winner: **${winner.callsign}**\n` +
        `Laps: ${winner.laps}\n` +
        `Time: ${winner.total_time}\n` +
        `Fastest Lap: ${winner.fastest_lap}`
    );
});

// Announce when pilots are up next
socket.on('heat_stage', (data) => {
    const channel = discordBot.channels.cache.get(RACE_CHANNEL_ID);
    const pilots = data.heat.pilots;

    channel.send(
        `⚠️ **Next Heat Starting Soon!**\n\n` +
        `Pilots: ${pilots.map(p => `<@${p.discord_id}>`).join(', ')}\n` +
        `Please be ready at your station!`
    );
});
```

---

### 4.2 Mobile Pilot App

**Use Case**: Pilots can view their schedule, stats, and get notifications through a mobile app.

**App Features**:
```javascript
// React Native / Flutter example
class PilotApp {
    constructor(pilotId) {
        this.pilotId = pilotId;
        this.socket = io('http://rotorhazard-server:5000');
        this.setupNotifications();
    }

    // Get pilot's upcoming heats
    async getMyHeats() {
        const allHeats = await this.fetchAllHeats();

        return allHeats.filter(heat =>
            heat.pilots.some(p => p.id === this.pilotId)
        ).map(heat => ({
            heat_id: heat.id,
            heat_name: heat.name,
            class: heat.class_name,
            slot: heat.pilots.findIndex(p => p.id === this.pilotId),
            scheduled_time: heat.scheduled_time,
            frequency: heat.slot_frequencies[slot],
            status: this.getHeatStatus(heat)
        }));
    }

    // Get personal statistics
    async getMyStats() {
        const allRaces = await this.fetchRaceHistory();
        const myRaces = allRaces.filter(race =>
            race.pilots.includes(this.pilotId)
        );

        const myLaps = myRaces.flatMap(race =>
            race.laps.filter(lap => lap.pilot_id === this.pilotId)
        );

        return {
            total_races: myRaces.length,
            total_laps: myLaps.length,
            average_position: this.calculateAvgPosition(myRaces),
            best_lap_time: Math.min(...myLaps.map(l => l.time)),
            average_lap_time: this.average(myLaps.map(l => l.time)),
            consistency_score: this.calculateConsistency(myLaps),
            wins: myRaces.filter(r => r.position === 1).length,
            podiums: myRaces.filter(r => r.position <= 3).length,
            improvement_trend: this.calculateTrend(myLaps)
        };
    }

    setupNotifications() {
        // Notify when pilot is in next heat
        this.socket.on('heat_change', (data) => {
            if (this.isPilotInHeat(data.next_heat)) {
                this.sendPushNotification(
                    "You're up next!",
                    `Heat ${data.next_heat.name} starts in 5 minutes.\n` +
                    `Your frequency: ${data.pilot_frequency} MHz`
                );
            }
        });

        // Notify when results are available
        this.socket.on('race_save', (data) => {
            if (this.wasPilotInRace(data.race_id)) {
                const position = this.getMyPosition(data.results);

                this.sendPushNotification(
                    "Race Complete!",
                    `You finished in position ${position}`
                );
            }
        });
    }
}
```

**App Screens**:
1. **Dashboard**: Next heat, current rank, recent results
2. **Schedule**: All heats with pilot assignments
3. **Stats**: Personal analytics and trends
4. **History**: Past race results with detailed lap data
5. **Settings**: Notification preferences, frequency settings

---

## 5. Spectator Experience

### 5.1 Interactive Spectator Display

**Use Case**: Large screens at the event showing live data, pilot profiles, and race replays.

**Display Modes**:
```javascript
class SpectatorDisplay {
    constructor() {
        this.currentMode = 'live_race';
        this.modes = {
            live_race: this.renderLiveRace.bind(this),
            pilot_profile: this.renderPilotProfile.bind(this),
            race_replay: this.renderRaceReplay.bind(this),
            leaderboard: this.renderLeaderboard.bind(this)
        };
    }

    // Mode 1: Live Race
    renderLiveRace() {
        socket.on('laps', (data) => {
            this.updateLiveLeaderboard(data);
            this.showLapTimeComparison(data);
            this.highlightFastestLap(data);

            // Show split times
            this.displaySplitTimes(data);
        });

        // Visual enhancements
        this.showPilotCameras();
        this.displayLapCounter();
        this.showRaceTimer();
    }

    // Mode 2: Pilot Profile Carousel
    async renderPilotProfile(pilotId) {
        const pilot = await this.getPilotData(pilotId);

        return {
            layout: 'profile',
            data: {
                callsign: pilot.callsign,
                team: pilot.team,
                country: pilot.country,
                avatar: `/shared/avatars/${pilot.id}.jpg`,
                stats: {
                    season_wins: 12,
                    best_lap_today: "26.12s",
                    current_rank: 2,
                    total_races: 45
                },
                achievements: [
                    "🏆 2025 Regional Champion",
                    "⚡ Fastest Qualifier Award",
                    "🎯 Most Consistent Pilot"
                ],
                sponsors: pilot.sponsors,
                equipment: {
                    frame: "5-inch Freestyle",
                    motors: "2306 2400KV",
                    fc: "F7 Flight Controller",
                    vtx: "800mW"
                }
            }
        };
    }

    // Mode 3: Race Replay
    async renderRaceReplay(raceId) {
        const raceData = await this.getRaceData(raceId);
        const timeline = this.buildRaceTimeline(raceData);

        // Playback controls
        this.replaySpeed = 1.0; // Normal speed
        this.showPilotPaths = true;
        this.showSplitTimes = true;

        timeline.forEach((event, index) => {
            setTimeout(() => {
                this.renderTimelineEvent(event);
            }, event.timestamp * this.replaySpeed);
        });
    }

    buildRaceTimeline(raceData) {
        const timeline = [];

        timeline.push({
            time: 0,
            event: 'race_start',
            data: { pilots: raceData.pilots }
        });

        raceData.laps.forEach(lap => {
            timeline.push({
                time: lap.timestamp,
                event: 'lap_complete',
                data: {
                    pilot: lap.pilot_callsign,
                    lap_number: lap.lap_number,
                    lap_time: lap.lap_time,
                    position: lap.position
                }
            });
        });

        timeline.push({
            time: raceData.end_time,
            event: 'race_finish',
            data: { results: raceData.final_results }
        });

        return timeline;
    }
}
```

---

### 5.2 Race Prediction Game

**Use Case**: Spectators predict race outcomes for an engaging interactive experience.

**Implementation**:
```javascript
class PredictionGame {
    constructor() {
        this.predictions = new Map();
        this.leaderboard = [];
        this.setupListeners();
    }

    setupListeners() {
        // Open predictions when race is staged
        socket.on('race_stage', (data) => {
            this.openPredictions(data.heat_info);
        });

        // Close predictions when race starts
        socket.on('race_start', (data) => {
            this.closePredictions();
        });

        // Score predictions when race completes
        socket.on('race_save', (data) => {
            this.scorePredictions(data.results);
        });
    }

    openPredictions(heatInfo) {
        const predictionWindow = {
            heat_id: heatInfo.id,
            heat_name: heatInfo.name,
            pilots: heatInfo.pilots,
            closing_time: Date.now() + 60000, // 1 minute
            prediction_options: {
                winner: heatInfo.pilots.map(p => p.callsign),
                podium: heatInfo.pilots.map(p => p.callsign),
                fastest_lap: heatInfo.pilots.map(p => p.callsign)
            }
        };

        this.displayPredictionForm(predictionWindow);
    }

    submitPrediction(spectatorId, predictions) {
        const pred = {
            spectator_id: spectatorId,
            heat_id: this.currentHeatId,
            timestamp: Date.now(),
            predictions: {
                winner: predictions.winner,
                podium: predictions.podium, // Top 3 in order
                fastest_lap: predictions.fastest_lap
            },
            confidence: predictions.confidence || 0.5
        };

        this.predictions.set(spectatorId, pred);
        return pred;
    }

    scorePredictions(results) {
        const actualWinner = results[0].callsign;
        const actualPodium = results.slice(0, 3).map(r => r.callsign);
        const actualFastestLap = results.reduce((fastest, r) =>
            r.fastest_lap < fastest.fastest_lap ? r : fastest
        ).callsign;

        this.predictions.forEach((pred, spectatorId) => {
            let score = 0;

            // Winner prediction (50 points)
            if (pred.predictions.winner === actualWinner) {
                score += 50;
            }

            // Podium prediction (10 points per correct,
            // 5 bonus for correct position)
            pred.predictions.podium.forEach((predicted, index) => {
                if (actualPodium.includes(predicted)) {
                    score += 10;
                    if (actualPodium[index] === predicted) {
                        score += 5;
                    }
                }
            });

            // Fastest lap prediction (25 points)
            if (pred.predictions.fastest_lap === actualFastestLap) {
                score += 25;
            }

            // Confidence multiplier
            score *= pred.confidence;

            this.updateLeaderboard(spectatorId, score);
        });

        this.displayResults();
    }

    updateLeaderboard(spectatorId, score) {
        const existing = this.leaderboard.find(
            entry => entry.spectator_id === spectatorId
        );

        if (existing) {
            existing.total_score += score;
            existing.predictions_made += 1;
            existing.accuracy = existing.total_score /
                               (existing.predictions_made * 100);
        } else {
            this.leaderboard.push({
                spectator_id: spectatorId,
                total_score: score,
                predictions_made: 1,
                accuracy: score / 100
            });
        }

        this.leaderboard.sort((a, b) => b.total_score - a.total_score);
    }
}
```

**Leaderboard Output**:
```json
{
  "game_leaderboard": [
    {
      "spectator_id": "user123",
      "spectator_name": "RaceFan42",
      "total_score": 485,
      "predictions_made": 8,
      "accuracy": 0.76,
      "rank": 1
    },
    {
      "spectator_id": "user456",
      "spectator_name": "FPVEnthusiast",
      "total_score": 420,
      "predictions_made": 7,
      "accuracy": 0.71,
      "rank": 2
    }
  ]
}
```

---

## API Reference Quick Guide

### Core Socket.IO Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `stage_race` | Emit | Prepare race for start |
| `stop_race` | Emit | Stop active race |
| `save_laps` | Emit | Commit race results |
| `race_start` | Listen | Race has started |
| `laps` | Listen | New lap completed |
| `race_status` | Listen | Race status changed |
| `leaderboard` | Listen | Position updates |
| `add_pilot` | Emit | Create new pilot |
| `alter_pilot` | Emit | Update pilot info |
| `set_frequency` | Emit | Assign node frequency |
| `export_database` | Emit | Export all data |

### Common Data Structures

**Pilot Object**:
```json
{
  "id": 1,
  "callsign": "SkyRacer",
  "team": "TeamFPV",
  "phonetic": "Sky Racer",
  "country": "US",
  "preferred_frequency": 5658
}
```

**Heat Object**:
```json
{
  "id": 5,
  "name": "Heat 3",
  "class_id": 1,
  "class_name": "Open Class",
  "pilots": [1, 3, 5, 7],
  "slot_assignments": [
    {"slot": 0, "pilot_id": 1, "frequency": 5658},
    {"slot": 1, "pilot_id": 3, "frequency": 5695}
  ]
}
```

**Race Results**:
```json
{
  "race_id": 42,
  "heat_id": 5,
  "results": [
    {
      "position": 1,
      "pilot_id": 1,
      "callsign": "SkyRacer",
      "laps": 7,
      "total_time": "3:15.234",
      "fastest_lap": "26.12",
      "average_lap": "27.89"
    }
  ]
}
```

---

## Best Practices

1. **Connection Management**
   - Always handle disconnect/reconnect scenarios
   - Implement exponential backoff for reconnection
   - Show connection status to users

2. **Error Handling**
   - Listen for error events from Socket.IO
   - Validate data before sending to API
   - Provide user feedback on failures

3. **Performance**
   - Throttle rapid UI updates
   - Use efficient data structures
   - Cache frequently accessed data

4. **Security**
   - Never expose admin credentials
   - Validate all user inputs
   - Use proper authentication for sensitive operations

5. **User Experience**
   - Show loading states
   - Provide real-time feedback
   - Handle edge cases gracefully

---

## Additional Resources

- **Testing Webapp**: `/ddr_overlays/api-tester`
- **RotorHazard GitHub**: https://github.com/RotorHazard/RotorHazard
- **API Documentation**: https://github.com/RotorHazard/RotorHazard/blob/main/doc/RHAPI.md
- **Plugin Guide**: https://github.com/RotorHazard/RotorHazard/blob/main/doc/Plugins.md

---

**Created**: 2026-01-14
**Last Updated**: 2026-01-14
**Version**: 1.0
