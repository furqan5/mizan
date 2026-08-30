function w = ws(T, p, aw)
%WS Saturation humidity ratio [kg/kg dry air] at temperature T [degC].
%   AW is the WATER ACTIVITY of the liquid (1.0 for pure water). Dissolved
%   salts depress the equilibrium vapour pressure to aw*pws -- this is the
%   single hook through which water chemistry couples back into the
%   thermal model.
if nargin < 2 || isempty(p),  p  = 101325.0; end
if nargin < 3 || isempty(aw), aw = 1.0;      end
pv = aw .* mizan.pws(T);
w = 0.621945 .* pv ./ (p - pv);
end
