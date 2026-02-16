import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass
from ..models.structures import B2BZoneInfo, SignalDirection, FlowState

class StrategyOrchestrator:
    """
    The BRAIN of the SIGMA Strategy.
    V2.1 Hybrid Logic: Fluid Origin + Fresh & Nested Traps.
    """
    
    def __init__(self, tf_state=None):
        self.tf_state = tf_state
        self.states: Dict[str, FlowState] = {
            'MN1': FlowState(),
            'W1': FlowState(),
            'D1': FlowState(),
            'H4': FlowState(),
            'H1': FlowState(),
            'M30': FlowState()
        }
        
    def update_flow_state(self, tf_zones: Dict[str, List[B2BZoneInfo]], current_price: float, current_time: pd.Timestamp):
        for tf in self.states.keys():
            self._update_flow(tf, tf_zones.get(tf, []), current_price)
            
        # V5.9: Heartbeat Parity
        if current_time.minute % 30 == 0 and current_time.second == 0:
            self._print_heartbeat(current_time)

    def _get_zone_by_id(self, zone_id: str, zones: List[B2BZoneInfo]) -> Optional[B2BZoneInfo]:
        for z in zones:
            if z.zone_id == zone_id:
                return z
        return None

    def _get_latest_outpost(self, tf: str, direction: SignalDirection, current_price: float, after_time: pd.Timestamp, zones: List[B2BZoneInfo]) -> Optional[str]:
        best_zone = None
        best_time = after_time
        for z in zones:
            if z.timeframe != tf or z.direction != direction or not z.is_valid:
                continue
            if z.zone_created_time > best_time:
                best_time = z.zone_created_time
                best_zone = z
        if best_zone:
            is_broken = (direction == SignalDirection.BULLISH and current_price < best_zone.L2_price) or \
                        (direction == SignalDirection.BEARISH and current_price > best_zone.L2_price)
            if is_broken: return None
            return best_zone.zone_id
        return None

    def _is_inside_opposing_zone(self, signal_tf: str, direction: SignalDirection, current_price: float, zones: List[B2BZoneInfo]) -> str:
        if signal_tf == 'MN1': return ""
        check_mn1 = True
        check_w1 = (signal_tf in ['D1', 'H4', 'H1', 'M30'])
        for z in zones:
            if not z.is_valid or z.direction == direction: continue
            tf_match = False
            if check_mn1 and z.timeframe == 'MN1': tf_match = True
            if check_w1 and z.timeframe == 'W1': tf_match = True
            if not tf_match: continue
            if z.L2_touched: continue
            high = max(z.L1_price, z.L2_price)
            low = min(z.L1_price, z.L2_price)
            if low <= current_price <= high:
                return z.zone_id
        return ""

    def _update_flow(self, tf: str, zones: List[B2BZoneInfo], current_price: float):
        state = self.states[tf]
        
        # 1. Sticky Validation: Keep current origin if valid and not broken
        if state.is_valid and state.origin_id != "":
            curr = self._get_zone_by_id(state.origin_id, zones)
            if curr and curr.is_valid:
                is_broken = (curr.direction == SignalDirection.BULLISH and current_price < curr.L2_price) or \
                             (curr.direction == SignalDirection.BEARISH and current_price > curr.L2_price)
                if not is_broken:
                    # Update Anchor Status
                    outpost_id = self._get_latest_outpost(tf, state.origin_dir, current_price, curr.zone_created_time, zones)

                    # V5.6.4: STRICT LINEAR LOGIC (Zombie Fix)
                    # If get_latest_outpost returns None (0), it means the trend leg is broken.
                    # We must reset the state if the outpost search failed (returned None usually implies failure or no outpost)
                    # Note: get_latest_outpost returns zone_id or None.
                    
                    state.outpost_id = outpost_id or ""
                    anchor = self._get_zone_by_id(outpost_id, zones) if outpost_id else curr
                    if outpost_id:
                        state.outpost_touch_time = anchor.L1_touch_time # V5.7

                    # V5.7: SAFETY TRIGGER (Anchor Must Be Traded)
                    # MQL5 Parity: Simply assigning current status is correct.
                    # Remove the 'is_ahead' heuristic for persisting zones.
                    state.anchor_is_traded = anchor.L1_touched

                    self._update_magnet_and_roadblock(tf, state, current_price, zones)
                    
                    # V5.5 SIEGE TRIGGER
                    # Logic: Magnet Hit -> Bounce -> Outpost Confirmed.
                    # If Outpost touch is FRESHER than Magnet touch => SIEGE MODE ACTIVE.
                    if state.magnet_id != "":
                         magnet_zone = self._get_zone_by_id(state.magnet_id, zones)
                         if magnet_zone and magnet_zone.L1_touched:
                             # Safe Comparison for timestamps
                             op_time = state.outpost_touch_time if state.outpost_touch_time is not None else pd.Timestamp.min
                             mg_time = magnet_zone.L1_touch_time if magnet_zone.L1_touch_time is not None else pd.Timestamp.min
                             
                             if op_time > mg_time:
                                 state.is_siege_active = True
                             else:
                                 state.is_siege_active = False
                    else:
                         state.is_siege_active = False

                    # Check Successor (Magnet Touch) - V5.4
                    if state.magnet_L2_touched:
                        successor_id = self._get_latest_outpost(tf, state.origin_dir, current_price, curr.zone_created_time, zones)
                        if successor_id:
                             # Promote Successor
                             state.origin_id = successor_id
                             state.magnet_id = ""
                             state.is_siege_active = False
                             # Successor inherits status
                             succ = self._get_zone_by_id(successor_id, zones)
                             state.anchor_is_traded = succ.L1_touched if succ else False
                             return # New Origin established, next tick will process it
                        else:
                             # V5.8: ATH Discovery Protection
                             # If no successor, but at ATH (MN1 Magnet 0), keep origin.
                             if self.states['MN1'].magnet_id == "" and tf in ['D1', 'W1', 'H4', 'H1', 'M30']:
                                 state.magnet_id = ""
                                 state.is_siege_active = False
                             else:
                                 state.is_valid = False # Valid Defeat
                                 state.reset()
                             return

                    return

        # 2. Origin Search (Sticky/Selective)
        best_origin = None
        for z in zones:
            if z.timeframe != tf or not z.is_valid: continue
            
            # V5.8: Macro Direction Preference in Discovery Mode (ATH/ATL)
            # REMOVED: This creates the "Discovery Lock" during market crashes.
            # D1/W1 should be allowed to lead the trend reversal.

            is_broken = (z.direction == SignalDirection.BULLISH and current_price < z.L2_price) or \
                         (z.direction == SignalDirection.BEARISH and current_price > z.L2_price)
            if is_broken: continue
            
            # In Media Res: Allow starting simulation past L1 for Macro Tiers
            is_ahead = (z.direction == SignalDirection.BULLISH and current_price > z.L1_price) or \
                        (z.direction == SignalDirection.BEARISH and current_price < z.L1_price)
            
            if not z.L1_touched and not is_ahead: continue
            
            # We want the MOST RECENT valid zone to establish the CURRENT macro bias
            if not best_origin or z.zone_created_time > best_origin.zone_created_time:
                best_origin = z
        
        if not best_origin:
            state.is_valid = False
            return

        state.origin_id = best_origin.zone_id
        state.origin_dir = best_origin.direction
        state.details_origin_price = best_origin.L1_price
        state.details_origin_L2 = best_origin.L2_price
        state.origin_touch_time = best_origin.L1_touch_time or best_origin.zone_created_time
        state.is_valid = True
        
        # Initial Anchor Status
        outpost_id = self._get_latest_outpost(tf, state.origin_dir, current_price, best_origin.zone_created_time, zones)
        state.outpost_id = outpost_id or ""
        anchor = self._get_zone_by_id(outpost_id, zones) if outpost_id else best_origin
        if outpost_id: state.outpost_touch_time = anchor.L1_touch_time

        # Initial Anchor Status
        state.anchor_is_traded = anchor.L1_touched
        state.is_siege_active = False # Fresh origin = No siege
            
        self._update_magnet_and_roadblock(tf, state, current_price, zones)

    def _update_magnet_and_roadblock(self, tf: str, state: FlowState, current_price: float, zones: List[B2BZoneInfo]):
        # Magnet Search
        best_magnet = None
        min_dist = float('inf')
        target_dir = SignalDirection.BEARISH if state.origin_dir == SignalDirection.BULLISH else SignalDirection.BULLISH
        for z in zones:
            if z.timeframe != tf or not z.is_valid or z.direction != target_dir: continue
            dist = float('inf')
            if state.origin_dir == SignalDirection.BULLISH:
                if z.L1_price > current_price: dist = z.L1_price - current_price
            else:
                if z.L1_price < current_price: dist = current_price - z.L1_price
            if dist < min_dist:
                min_dist = dist
                best_magnet = z
        
        if best_magnet:
            state.magnet_id = best_magnet.zone_id
            state.magnet_dir = best_magnet.direction 
            state.details_magnet_price = best_magnet.L1_price # Added to match MQL5
            state.details_magnet_L2 = best_magnet.L2_price
            state.magnet_fifty_touched = best_magnet.fifty_touched
            state.magnet_L2_touched = best_magnet.L2_touched
            
            # V5.8: Structural Supremacy (Highest Magnet)
            state.is_magnet_extreme = True
            for z in zones:
                if z.timeframe == tf and z.direction == state.magnet_dir and z.is_valid:
                    if state.magnet_dir == SignalDirection.BEARISH:
                        if z.L1_price > state.details_magnet_price:
                             state.is_magnet_extreme = False
                             break
                    else:
                        if z.L1_price < state.details_magnet_price:
                             state.is_magnet_extreme = False
                             break
        else:
            state.magnet_id = ""
            state.details_magnet_L2 = 0.0
            state.magnet_fifty_touched = False
            state.magnet_L2_touched = False
            state.is_magnet_extreme = False
            
        # Global Roadblock: Check ALL timeframes for opposing zones
        state.roadblock_id = self._is_inside_opposing_zone(tf, state.origin_dir, current_price, zones, siege_magnet_id=state.magnet_id if state.is_siege_active else "")

    def _validate_trap(self, trap: B2BZoneInfo, narrative: FlowState, flow_tf: str) -> bool:
        if trap.direction != narrative.origin_dir: return False
        
        # Guard 1: Freshness (Timing)
        # V5.6.5: RELATIVE FRESHNESS (Stale Trap Fix)
        # - If Free Flow (Outpost > 0): Trap must be newer than OUTPOST. (Current Leg)
        # - If Strict Mode (Outpost == 0): Trap must be newer than ORIGIN. (Initial reaction)
        
        # FIX V5.6.5: Falling Knife Protection.
        # We use OUTPOST TOUCH TIME, not CREATION TIME.
        freshness_baseline = narrative.origin_touch_time
        if narrative.outpost_id != "":
            # MQL5 Parity: If Outpost exists but hasn't been touched, we default baseline to Current Time
            # effectively BLOCKING all past traps. (Safety Trigger)
            if narrative.outpost_touch_time is not None and narrative.outpost_touch_time > pd.Timestamp.min:
                 freshness_baseline = narrative.outpost_touch_time
            else:
                 # Untouched Outpost -> Block All Traps
                 return False
        
        if trap.zone_created_time <= freshness_baseline:
            return False
            
        # V5.7.1: Strict Nesting Buffer Logic
        # MQL5 uses _Point. For Python backtester, we use 0.0 to match the 'Strict' intent.
        epsilon = 0.0

        # Roadblock Filter (V2.0 Core) - Kept inside for safety, though MQL5 checks outside.
        if narrative.roadblock_id != "":
            return False

        # Conscious Hierarchy Check: If this is H4/H1/M30, it must align with D1/W1
        if flow_tf in ['H4', 'H1', 'M30']:
            # Check D1 Alignment
            d1 = self.states['D1']
            if not d1.is_valid or trap.direction != d1.origin_dir:
                return False
            # Check W1 Alignment
            w1 = self.states['W1']
            if not w1.is_valid or trap.direction != w1.origin_dir:
                return False

        # Shield Check
        mn1 = self.states['MN1']
        w1_s = self.states['W1']
        mn1_shield = mn1.is_valid and (mn1.magnet_fifty_touched or mn1.magnet_L2_touched)
        w1_shield = w1_s.is_valid and (w1_s.magnet_fifty_touched or w1_s.magnet_L2_touched)
        if mn1_shield: return False
        if flow_tf == 'D1' and w1_shield: return False
        
        # V5.7: TRAP LIBERATION (Safety First)
        # If Outpost exists AND has been traded (Safety Trigger), we allow Continuation.
        # If No Outpost OR Outpost untraded, we require Strict Nesting.
        is_free_flow = (narrative.outpost_id != "" and narrative.anchor_is_traded)
        
        if is_free_flow:
             # FREE FLOW MODE (Continuation)
             # Constraint: Local Magnet Fade Check (Moving "Anti-Fade" here)
             if (narrative.magnet_fifty_touched or narrative.magnet_L2_touched) and not narrative.is_siege_active:
                 return False # BLOCKED: Local Magnet is Fading.
        else:
             # STRICT MODE (Refusing to lose)
             # No Outpost = No Trend. We force strict spatial nesting inside Origin.
              if trap.direction == SignalDirection.BULLISH:
                  if trap.L1_price > narrative.details_origin_price + epsilon: return False
              else:
                  if trap.L1_price < narrative.details_origin_price - epsilon: return False
            
        return True

    def _get_officer_target(self) -> float:
        for tf in ['H4', 'H1', 'M30']:
            st = self.states[tf]
            if st.is_valid and st.details_magnet_L2 > 0:
                return st.details_magnet_L2
        return 0.0

    def is_trade_allowed(self, signal_tf: str, direction: SignalDirection, zone: B2BZoneInfo, current_price: float, probe_price: Optional[float] = None) -> tuple[bool, str, float]:
        """
        The GATEKEEPER.
        Checks if a signal is authorized by the HTF narrative and local structural context.
        probe_price: Used for Wick-Aware scanning (High/Low of bar)
        """
        # If no probe_price provided, default to current_price (bar close)
        eval_price = probe_price if probe_price is not None else current_price

        # Sniper Constraint (MQL5 Parity V5.0): 
        # GENERALS (MN1, W1, D1) DO NOT FIRE. They provide Context.
        # OFFICERS (H4, H1, M30...) FIRE TRADES.
        if signal_tf not in ['H4', 'H1', 'M30', 'M15', 'M5', 'M1']:
            return False, "TF Restricted (Context Only - Generals Don't Fight)", 0.0

        # === PRE-FLIGHT: STATE ASSIGNMENT ===
        mn1 = self.states['MN1']
        w1 = self.states['W1']
        d1 = self.states['D1']
        
        # === V5.7 HANDOVER LOGIC (Freshness Protocol) ===
        d1_fresh_override = False
        w1_fresh_override = False
        
        if d1.is_valid and d1.origin_dir == direction:
            if mn1.is_valid and d1.origin_dir == mn1.origin_dir and d1.origin_touch_time > mn1.origin_touch_time: d1_fresh_override = True
            if w1.is_valid and d1.origin_dir == w1.origin_dir and d1.origin_touch_time > w1.origin_touch_time: d1_fresh_override = True
            
        if w1.is_valid and w1.origin_dir == direction:
            if mn1.is_valid and w1.origin_dir == mn1.origin_dir and w1.origin_touch_time > mn1.origin_touch_time: w1_fresh_override = True

        authorized = False
        target_price = 0.0
        reason = ""

        # === 1. ANTI-TREND FADERS (Siege Bypass) ===
        # These gates authorize trades AGAINST the dominant trend when price hits a major magnet core.
        # They MUST bypass the Siege Guard because sieges are triggered by the exact same magnet touches.
        
        # A. AGGRESSIVE PULLBACK (MN1 Core Fade)
        if not authorized and mn1.is_valid and (mn1.magnet_fifty_touched or mn1.magnet_L2_touched):
            mag_fifty = mn1.details_magnet_price + (mn1.details_magnet_L2 - mn1.details_magnet_price) * 0.5
            core_high = max(mn1.details_magnet_L2, mag_fifty)
            core_low = min(mn1.details_magnet_L2, mag_fifty)
            if core_low <= eval_price <= core_high and direction != mn1.origin_dir:
                 authorized = True
                 reason = "Aggressive Magnet Fade (Core T2/T3 Only)"
                 target_price = 0.0

        # B. W1 MAGNET FADE (V5.8)
        if not authorized and w1.is_valid and (w1.magnet_fifty_touched or w1.magnet_L2_touched):
             mag_fifty = w1.details_magnet_price + (w1.details_magnet_L2 - w1.details_magnet_price) * 0.5
             core_high = max(w1.details_magnet_L2, mag_fifty)
             core_low = min(w1.details_magnet_L2, mag_fifty)
             if core_low <= eval_price <= core_high and direction != w1.origin_dir:
                 authorized = True
                 reason = "W1 Magnet Fade (V5.8)"
                 target_price = 0.0

        # C. D1 ATH MAGNET FADE (V5.8)
        if not authorized and d1.is_valid and mn1.magnet_id == "" and (d1.magnet_fifty_touched or d1.magnet_L2_touched):
             mag_fifty = d1.details_magnet_price + (d1.details_magnet_L2 - d1.details_magnet_price) * 0.5
             core_high = max(d1.details_magnet_L2, mag_fifty)
             core_low = min(d1.details_magnet_L2, mag_fifty)
             if d1.is_magnet_extreme and core_low <= eval_price <= core_high and direction != d1.origin_dir:
                 authorized = True
                 reason = "D1 ATH Magnet Fade (V5.8)"
                 target_price = 0.0

        if authorized:
            return True, reason, target_price

        # === 2. GLOBAL SIEGE GUARD (Trend Safety) ===
        # Blocks trend-following trades that are joining a crowded or overextended 'Siege'.
        if mn1.is_siege_active and direction != mn1.origin_dir: return False, "Global Siege Block_MN1", 0.0
        if w1.is_siege_active and direction != w1.origin_dir: return False, "Global Siege Block_W1", 0.0
        if d1.is_siege_active and direction != d1.origin_dir: return False, "Global Siege Block_D1", 0.0

        # === 3. TREND-FOLLOWING FLOWS ===
        # A. MN1 AUTHORITY (The Tide)
        if not d1_fresh_override and not w1_fresh_override and mn1.is_valid and mn1.origin_dir == direction:
             if self._validate_trap(zone, mn1, 'MN1'):
                 authorized = True
                 target_price = 0.0 
                 reason = "MN1 Flow (Tide)"
                 if mn1.details_magnet_L2 == 0: reason += " (Discovery)"

        # B. W1 AUTHORITY (The Wave)
        if not authorized and not d1_fresh_override and w1.is_valid:
            if self._validate_trap(zone, w1, 'W1'):
                # Check for W1 Pullback (Magnet Reaction)
                if mn1.is_valid and w1.origin_dir != mn1.origin_dir:
                    if (mn1.magnet_fifty_touched or mn1.magnet_L2_touched):
                         mag_fifty = mn1.details_magnet_price + (mn1.details_magnet_L2 - mn1.details_magnet_price) * 0.5
                         core_high = max(mn1.details_magnet_L2, mag_fifty)
                         core_low = min(mn1.details_magnet_L2, mag_fifty)
                         if core_low <= eval_price <= core_high:
                             authorized = True
                             reason = "W1 Pullback (Magnet Reaction)"
                             target_price = 0.0
                else:
                    if w1.roadblock_id == "":
                        authorized = True
                        reason = "W1 Flow (Handover)" if w1_fresh_override else "W1 Flow"
                        target_price = 0.0
                        if w1.details_magnet_L2 == 0: reason += " (Discovery)"

        # C. D1 AUTHORITY (The Path)
        if not authorized and d1.is_valid:
            if self._validate_trap(zone, d1, 'D1'):
                if d1.roadblock_id == "":
                    authorized = True
                    reason = "D1 Flow (Handover)" if d1_fresh_override else "D1 Flow"
                    target_price = 0.0
                    if d1.details_magnet_L2 == 0: reason += " (Discovery)"

        if not authorized:
            return False, "No Authority or Strategy Alignment", 0.0
            
        return True, reason, target_price

    def _print_heartbeat(self, current_time: pd.Timestamp):
        """MQL5 Heartbeat Parity: Console logging of flow state."""
        mn = self.states['MN1']
        w1 = self.states['W1']
        d1 = self.states['D1']
        h4 = self.states['H4']
        h1 = self.states['H1']
        m3 = self.states['M30']
        
        print(f"\n[{current_time}] === V5.9 ORCHESTRATOR HEARTBEAT ===")
        print(f"MN1 Tide: {mn.origin_dir.value if mn.is_valid else 'INVALID'} | Origin: #{mn.origin_id[:4]} -> Magnet: #{mn.magnet_id[:4]}")
        print(f"W1 Wind:  {w1.origin_dir.value if w1.is_valid else 'INVALID'} | Origin: #{w1.origin_id[:4]} -> Magnet: #{w1.magnet_id[:4]}")
        print(f"D1 Path:  {d1.origin_dir.value if d1.is_valid else 'INVALID'} | Origin: #{d1.origin_id[:4]} -> Magnet: #{d1.magnet_id[:4]}")
        print(f">>> OFFICERS: H4:#{h4.origin_id[:4]} | H1:#{h1.origin_id[:4]} | M30:#{m3.origin_id[:4]}")


    # V5.4: Location Filter (Are we INSIDE an enemy zone?)
    # V5.5: SIEGE MODE - If siege_magnet_id != "", we IGNORE that specific zone if it's the valid blocker.
    def _is_inside_opposing_zone(self, tf: str, direction: SignalDirection, price: float, zones: List[B2BZoneInfo], siege_magnet_id: str = "") -> str:
        opp_dir = SignalDirection.BEARISH if direction == SignalDirection.BULLISH else SignalDirection.BULLISH
        blocked_by = ""
        
        # Rule:
        # MN1 Trade: Ignores everything (Returns "")
        # W1 Trade: Checks MN1 Opposing Zone.
        # D1 Trade: Checks W1 & MN1 Opposing Zones.
        if tf == 'MN1': return ""
        
        check_mn1 = True
        check_w1 = (tf == 'D1')
        
        for z in zones:
            if not z.is_valid: continue
            if z.direction != opp_dir: continue # Ignore same-direction zones

            # Strict Hierarchy Check (MQL5 Parity)
            # We ONLY check superior officers.
            tf_match = False
            if check_mn1 and z.timeframe == 'MN1': tf_match = True
            if check_w1 and z.timeframe == 'W1': tf_match = True
            
            if not tf_match: continue
                
            # V5.7: BULLDOZER MODE - If zone is pierced (L2 Touched), it's not a wall.
            if z.L2_touched: continue

            # Location Check: Is current_price INSIDE L1-L2?
            high = max(z.L1_price, z.L2_price)
            low = min(z.L1_price, z.L2_price)
            
            if low <= price <= high:
                # 3.2 BULLDOZER MODE: We are inside the enemy base, BUT Siege is active.
                # We IGNORE this specific blocker to allow the break.
                if siege_magnet_id != "" and z.zone_id == siege_magnet_id:
                    continue
                
                blocked_by = z.zone_id
                break
                
        return blocked_by

