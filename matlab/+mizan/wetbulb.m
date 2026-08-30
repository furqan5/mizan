function Twb = wetbulb(T, W, p)
%WETBULB Thermodynamic wet-bulb [degC] from dry-bulb and humidity ratio.
%   Inverts ASHRAE Eq. (33)/(34) by bracketed root find. The residual is
%   monotone in Twb over (-100 degC, T], so the bracket is safe.
if nargin < 3 || isempty(p), p = 101325.0; end
f = @(twb) mizan.w_from_wetbulb(T, twb, p) - W;
lo = -100.0; hi = T;
if f(lo)*f(hi) > 0
    Twb = hi;  return
end
Twb = fzero(f, [lo hi], optimset('TolX', 1e-10));
end
