function [pH_limit, T_skin] = mizan_chem_step(T_hot, cycles)
%MIZAN_CHEM_STEP  The scaling limit at the condenser tube skin.
%   SKIN_DELTA_K is how much hotter the tube skin runs than the water
%   around it. 8 K is the fouled-tube figure used throughout this package.
%   It is the least-defended number in the chemistry chain and every result
%   scales with it; deriving it from boundary-layer CFD rather than from
%   literature convention is on the roadmap.
SKIN_DELTA_K = 8.0;
T_skin = T_hot + SKIN_DELTA_K;

% Aqueous chemistry is only defined where liquid water exists. A solver
% transient can briefly ask for a temperature no cooling loop reaches, and
% below about -150 C the Debye-Huckel permittivity correlation goes
% negative and the saturation pH comes back COMPLEX. Clamping to the liquid
% range is not a fudge -- it is saying that the question was not a chemistry
% question. Anything outside the clamp is reported through the supervisor's
% fault path, not silently used.
T_eval = min(max(T_skin, 0.0), 100.0);
w = mizan.water_aramco(cycles, 26.8);
pH_limit = real(mizan.ph_sat_brucite(T_eval, w));
if ~isfinite(pH_limit), pH_limit = 14.0; end
end
