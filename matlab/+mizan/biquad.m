function v = biquad(c, x, y)
%BIQUAD EnergyPlus bi-quadratic performance curve.
v = c(1) + c(2)*x + c(3)*x.^2 + c(4)*y + c(5)*y.^2 + c(6)*x.*y;
end
