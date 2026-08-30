function Twb = wetbulb_from_rh(T, rh, p)
%WETBULB_FROM_RH Wet-bulb [degC] from dry-bulb and relative humidity.
if nargin < 3 || isempty(p), p = 101325.0; end
Twb = mizan.wetbulb(T, mizan.w_from_rh(T, rh, p), p);
end
