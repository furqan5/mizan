function W = w_from_rh(T, rh, p)
%W_FROM_RH Humidity ratio from dry-bulb [degC] and relative humidity [0..1].
if nargin < 3 || isempty(p), p = 101325.0; end
pv = rh .* mizan.pws(T);
W = 0.621945 .* pv ./ (p - pv);
end
