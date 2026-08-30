function p = pws(T)
%PWS Saturation vapour pressure of water [Pa] at temperature T [degC].
%   ASHRAE Fundamentals 2017 Eq. (5) over ice and Eq. (6) over liquid
%   water, Hyland & Wexler basis. Ported from src/psychro.py; the two
%   implementations are cross-checked by MIZAN_VERIFY.
Tk = T + 273.15;
if T < 0
    lnp = -5.6745359e3./Tk + 6.3925247 - 9.677843e-3*Tk ...
          + 6.2215701e-7*Tk.^2 + 2.0747825e-9*Tk.^3 ...
          - 9.484024e-13*Tk.^4 + 4.1635019*log(Tk);
else
    lnp = -5.8002206e3./Tk + 1.3914993 - 4.8640239e-2*Tk ...
          + 4.1764768e-5*Tk.^2 - 1.4452093e-8*Tk.^3 ...
          + 6.5459673*log(Tk);
end
p = exp(lnp);
end
