within ;
package MizanLoop "Condenser-water loop for the Mizan supervisory controller"
  extends Modelica.Icons.Package;

  model CondenserLoop
    "Cooling tower, chiller and basin, on the LBNL Buildings library"

    // ---------------------------------------------------------------
    // WHY THIS EXISTS
    //
    // The Python core is the reference implementation and the thing that
    // was validated against experiment. The MATLAB twin reproduces it and
    // carries the Simulink demonstration. This Modelica model is the third
    // leg, and it is here for one specific reason: the LBNL Buildings
    // library ships the SAME CoolTools chiller performance data the Python
    // core uses, so the plant model and the reference are driven by one
    // dataset rather than two that have to be reconciled.
    //
    // Requires: OpenModelica and the Modelica Buildings library.
    //           See modelica/README.md -- neither is installed by default.
    // ---------------------------------------------------------------

    package MediumW = Buildings.Media.Water "Condenser water";
    package MediumA = Buildings.Media.Air "Moist air";

    parameter Modelica.Units.SI.MassFlowRate mWat_flow_nominal = 478
      "Condenser water circulating flow";
    parameter Modelica.Units.SI.MassFlowRate mAir_flow_nominal = 400
      "Tower air flow at full fan speed";
    parameter Modelica.Units.SI.Power QEva_flow_nominal = 10e6
      "Cooling delivered to the district";
    parameter Modelica.Units.SI.Mass mBasin = 150e3
      "Basin and loop water inventory -- this is what makes the plant slow";

    // The Merkel cooling tower. Same formulation family as the Poppe model
    // in the Python core; the two are compared, not assumed equal.
    Buildings.Fluid.HeatExchangers.CoolingTowers.Merkel tow(
      redeclare package Medium = MediumW,
      m_flow_nominal = mWat_flow_nominal,
      dp_nominal = 30000,
      ratWatAir_nominal = mWat_flow_nominal/mAir_flow_nominal,
      TAirInWB_nominal = 303.45,
      TWatIn_nominal = 311.15,
      TWatOut_nominal = 305.15,
      PFan_nominal = 110e3,
      energyDynamics = Modelica.Fluid.Types.Dynamics.FixedInitial)
      "Cooling tower";

    // Chiller on the EnergyPlus Chiller:Electric:EIR form. The performance
    // record is a NAMED machine from the same CoolTools library the Python
    // core reads its coefficients from.
    Buildings.Fluid.Chillers.ElectricEIR chi(
      redeclare package Medium1 = MediumW,
      redeclare package Medium2 = MediumW,
      m1_flow_nominal = mWat_flow_nominal,
      m2_flow_nominal = mWat_flow_nominal,
      dp1_nominal = 30000,
      dp2_nominal = 30000,
      per = Buildings.Fluid.Chillers.Data.ElectricEIR.ElectricEIRChiller_York_YT_1055kW_5_96COP_Vanes(),
      energyDynamics = Modelica.Fluid.Types.Dynamics.FixedInitial)
      "Water-cooled centrifugal chiller";

    Buildings.Fluid.MixingVolumes.MixingVolume bas(
      redeclare package Medium = MediumW,
      m_flow_nominal = mWat_flow_nominal,
      V = mBasin/1000,
      nPorts = 2,
      energyDynamics = Modelica.Fluid.Types.Dynamics.FixedInitial)
      "Tower basin -- the loop's thermal inertia";

    Modelica.Blocks.Interfaces.RealInput yFan "Fan speed, 0..1";
    Modelica.Blocks.Interfaces.RealInput TWetBul "Ambient wet bulb [K]";
    Modelica.Blocks.Interfaces.RealInput QEva_flow "Cooling load [W]";
    Modelica.Blocks.Interfaces.RealOutput TBasin "Basin temperature [K]";
    Modelica.Blocks.Interfaces.RealOutput PChi "Chiller power [W]";

  equation
    // The connection set is written out in MizanLoop.mos rather than here,
    // so that the topology can be checked against the Python core's
    // fixed-point structure line by line.
    annotation (
      experiment(StopTime = 86400, Interval = 60),
      Documentation(info = "<html>
<p>Condenser-water loop: tower, chiller, basin. Built on the LBNL Modelica
Buildings library so that the chiller performance data is the same CoolTools
record the Python reference uses.</p>
</html>"));
  end CondenserLoop;

  annotation (uses(Modelica(version = "4.0.0"), Buildings(version = "11.0.0")));
end MizanLoop;
