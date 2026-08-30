function w = water_aramco(cycles, SiO2)
%WATER_ARAMCO Measured Saudi Aramco reclaimed water, concentrated by CYCLES.
%   Badruzzaman et al. (2022), Water Resources and Industry 28:100188,
%   closed on charge balance by sodium. Concentrations in mg/L.
%   SiO2 is not reported in the source and so is passed in explicitly
%   rather than invented; 26.8 mg/L is the Salbukh, Riyadh measurement
%   (Al-Mutaz & Al-Anezi 2004).
if nargin < 1 || isempty(cycles), cycles = 1.0; end
if nargin < 2 || isempty(SiO2),   SiO2   = 26.8; end
w.Ca = 94.0; w.Mg = 41.0; w.Na = 428.9; w.K = 25.0;
w.HCO3 = 70.0; w.SO4 = 566.0; w.Cl = 565.0; w.NO3 = 12.0;
w.SiO2 = SiO2;
f = fieldnames(w);
for i = 1:numel(f), w.(f{i}) = w.(f{i})*cycles; end
w.TDS = 1500.0*cycles;
w.cycles = cycles;
end
