function w = water_balance(m_evap, m_w, cycles, drift_fraction)
%WATER_BALANCE Steady-state loop water balance [kg/s].
%
%       makeup = evaporation + drift + blowdown
%       cycles = makeup / (blowdown + drift)
%
%   Evaporation leaves the salts behind so it does not appear in the cycles
%   ratio; drift does, because drift carries salt out with it.
%
%   DRIFT is quoted by manufacturers as a PERCENTAGE of circulating flow.
%   Modern high-efficiency eliminators are 0.0005 % to 0.001 %, i.e. 5e-6
%   to 1e-5 as a FRACTION. Both this model and the Python core once carried
%   0.0005 used directly as a fraction -- the rating with its percent sign
%   dropped, and a hundred times too much drift.
%
%   Note that drift cancels exactly out of makeup for as long as blowdown
%   stays positive, so makeup was never affected. What was wrong is the
%   reported BLOWDOWN, 27 % low at seven cycles, which is the quantity a
%   discharge permit is written against.
if nargin < 4 || isempty(drift_fraction), drift_fraction = 1.0e-5; end
cycles = max(cycles, 1.0001);
drift    = drift_fraction*m_w;
blowdown = max(m_evap/(cycles - 1.0) - drift, 0.0);
w.drift    = drift;
w.blowdown = blowdown;
w.makeup   = m_evap + drift + blowdown;
end
