function s = chiller()
%CHILLER Performance curves for a NAMED machine, not a generic curve set.
%
%   York YT, 1758 kW (500 TR) water-cooled centrifugal, inlet vanes,
%   reference COP 6.28 at the AHRI 550/590 rating point (6.67 degC leaving
%   chilled water, 29.44 degC entering condenser water).
%
%   Source: EnergyPlus reference dataset datasets/Chillers.idf, object
%   "ElectricEIRChiller York YT 1758kW/6.28COP/Vanes" (the CoolTools curve
%   library, shipped unchanged with every EnergyPlus release).
%
%   Chosen out of the 110 water-cooled centrifugals in that file because
%   (a) its reference point IS the AHRI rating point, (b) its curves are
%   fitted over 15.56-35.00 degC entering condenser water, which spans the
%   Gulf operating range where most of the library stops at 26.11 degC, and
%   (c) it is a vane-controlled centrifugal, the workhorse of Gulf district
%   cooling, rather than a high-COP variable-speed outlier.
%
%   The SAME numbers are in src/controller.py. MIZAN_VERIFY checks that.
s.name   = 'York YT 1758kW/6.28COP/Vanes (EnergyPlus Chillers.idf)';
s.capft  = [0.7079149, -0.002006276, -0.002596043, ...
            0.03005922, -0.001056423,  0.002045705];
s.eirft  = [0.5605391, -0.01377994,   6.569542e-05, ...
            0.01321951, 0.0002686074, -0.0005011451];
s.eirplr = [0.1861223,  0.5482049,    0.2647377];
s.cop_ref   = 6.28;
s.T_chws_ref = 6.67;
s.T_cws_ref  = 29.44;
s.T_chws_range = [4.44 8.89];      % fitted range in x
s.T_cws_range  = [15.56 35.00];    % fitted range in y AND the machine's
                                   % permitted entering-condenser window
s.plr_range    = [0.20 1.06];
end
