function W = w_from_wetbulb(T, Twb, p)
%W_FROM_WETBULB Humidity ratio from dry-bulb and thermodynamic wet-bulb.
%   ASHRAE Eq. (33) above freezing, Eq. (34) below.
if nargin < 3 || isempty(p), p = 101325.0; end
Wsw = mizan.ws(Twb, p, 1.0);
if Twb >= 0
    W = ((2501.0 - 2.326*Twb).*Wsw - 1.006*(T - Twb)) ./ ...
        (2501.0 + 1.86*T - 4.186*Twb);
else
    W = ((2830.0 - 0.24*Twb).*Wsw - 1.006*(T - Twb)) ./ ...
        (2830.0 + 1.86*T - 2.1*Twb);
end
W = max(W, 0.0);
end
