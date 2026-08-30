function Lef = lewis_factor(w, w_sw)
%LEWIS_FACTOR Bosnjakovic Lewis factor. Kloppers & Kroeger Eq. (5).
r = (w_sw + 0.622) ./ (w + 0.622);
r = max(r, 1.0 + 1e-12);
Lef = 0.865^(2.0/3.0) .* (r - 1.0) ./ log(r);
end
