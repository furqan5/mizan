function [P, COP, in_envelope] = chiller_power(Q_evap_kW, T_cws, T_chws, Q_ref_kW)
%CHILLER_POWER Chiller electrical power [kW], EnergyPlus Chiller:Electric:EIR.
%
%   IN_ENVELOPE is false when the entering condenser water temperature is
%   outside the range the curves were fitted in. That is not a nicety. Left
%   unchecked, the optimiser drives the fan to its lower bound, pushes
%   entering condenser water to 36-40 degC, and collects a large apparent
%   water saving from pure extrapolation. It did exactly that once.
%
%   The published curves return 0.950 (CAPFT) and 0.995 (EIRFT) at the AHRI
%   point rather than unity, because CoolTools fits were anchored to each
%   machine's own calibration point. Normalising preserves the curve SHAPE
%   -- how power varies with condenser temperature, the only quantity the
%   optimiser depends on -- while anchoring the magnitude to the machine's
%   stated reference COP.
if nargin < 3 || isempty(T_chws),  T_chws  = 7.0;        end
if nargin < 4 || isempty(Q_ref_kW), Q_ref_kW = Q_evap_kW; end
s = mizan.chiller();

in_envelope = T_cws >= s.T_cws_range(1) && T_cws <= s.T_cws_range(2);

capft_ref = mizan.biquad(s.capft, s.T_chws_ref, s.T_cws_ref);
eirft_ref = mizan.biquad(s.eirft, s.T_chws_ref, s.T_cws_ref);
capft = max(mizan.biquad(s.capft, T_chws, T_cws)/capft_ref, 0.3);
eirft = max(mizan.biquad(s.eirft, T_chws, T_cws)/eirft_ref, 0.3);

q_avail = Q_ref_kW*capft;
plr = min(max(Q_evap_kW/max(q_avail, 1e-6), 0.1), 1.0);
eirplr = (s.eirplr(1) + s.eirplr(2)*plr + s.eirplr(3)*plr^2)/sum(s.eirplr);

P = (Q_ref_kW/s.cop_ref)*capft*eirft*eirplr;
COP = Q_evap_kW/max(P, 1e-6);
end
