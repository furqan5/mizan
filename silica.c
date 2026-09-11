/* Main Simulation File */

#if defined(__cplusplus)
extern "C" {
#endif

#include "silica_model.h"
#include "simulation/solver/events.h"
#include "simulation/arrayIndex.h"

/* FIXME these defines are ugly and hard to read, why not use direct function pointers instead? */
#define prefixedName_performSimulation silica_performSimulation
#define prefixedName_updateContinuousSystem silica_updateContinuousSystem
#include <simulation/solver/perform_simulation.c.inc>

#define prefixedName_performQSSSimulation silica_performQSSSimulation
#include <simulation/solver/perform_qss_simulation.c.inc>


/* dummy VARINFO and FILEINFO */
const VAR_INFO dummyVAR_INFO = omc_dummyVarInfo;

int silica_input_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int silica_input_function_init(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int silica_input_function_updateStartValues(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int silica_inputNames(DATA *data, char ** names){
  
  return 0;
}

int silica_data_function(DATA *data, threadData_t *threadData)
{
  return 0;
}

int silica_dataReconciliationInputNames(DATA *data, char ** names){
  
  return 0;
}

int silica_dataReconciliationUnmeasuredVariables(DATA *data, char ** names)
{
  
  return 0;
}

int silica_output_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int silica_setc_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int silica_setb_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}


/*
equation index: 11
type: SIMPLE_ASSIGN
c_target = SR_setpoint * S_sat_mean
*/
void silica_eqFunction_11(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,11};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[8]] /* c_target variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* SR_setpoint PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* S_sat_mean variable */));
  threadData->lastEquationSolved = 11;
}

/*
equation index: 12
type: SIMPLE_ASSIGN
B = E / (-1.0 + c_target / c_m) - D
*/
void silica_eqFunction_12(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,12};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[3]] /* B variable */) = DIVISION_SIM((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[1]] /* E PARAM */),-1.0 + DIVISION_SIM((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[8]] /* c_target variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* c_m PARAM */),"c_m",equationIndexes),"-1.0 + c_target / c_m",equationIndexes) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[0]] /* D PARAM */);
  threadData->lastEquationSolved = 12;
}

/*
equation index: 13
type: SIMPLE_ASSIGN
$DER.c = ((E + B + D) * c_m + ((-B) - D) * c) / V
*/
void silica_eqFunction_13(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,13};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[1]] /* der(c) STATE_DER */) = DIVISION_SIM(((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[1]] /* E PARAM */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[3]] /* B variable */) + (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[0]] /* D PARAM */)) * ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* c_m PARAM */)) + ((-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[3]] /* B variable */)) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[0]] /* D PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[0]] /* c STATE(1) */)),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[5]] /* V PARAM */),"V",equationIndexes);
  threadData->lastEquationSolved = 13;
}

/*
equation index: 14
type: SIMPLE_ASSIGN
cycles = c / c_m
*/
void silica_eqFunction_14(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,14};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[9]] /* cycles variable */) = DIVISION_SIM((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[0]] /* c STATE(1) */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* c_m PARAM */),"c_m",equationIndexes);
  threadData->lastEquationSolved = 14;
}

/*
equation index: 15
type: SIMPLE_ASSIGN
$cse1 = cos(7.27220521664304e-5 * (time - t_peak))
*/
void silica_eqFunction_15(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,15};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[2]] /* $cse1 variable */) = cos((7.27220521664304e-5) * (data->localData[0]->timeValue - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[7]] /* t_peak PARAM */)));
  threadData->lastEquationSolved = 15;
}

/*
equation index: 16
type: SIMPLE_ASSIGN
T_basin = T_mean - T_amp * $cse1
*/
void silica_eqFunction_16(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,16};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* T_basin variable */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[4]] /* T_mean PARAM */) - (((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[3]] /* T_amp PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[2]] /* $cse1 variable */)));
  threadData->lastEquationSolved = 16;
}

/*
equation index: 17
type: SIMPLE_ASSIGN
S_sat = 60084.0 * 10.0 ^ (-2.71 + (-784.58) * (-0.0033540164346805303 + 1.0 / (273.15 + T_basin)))
*/
void silica_eqFunction_17(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,17};
  modelica_real tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  modelica_real tmp3;
  modelica_real tmp4;
  modelica_real tmp5;
  modelica_real tmp6;
  tmp0 = 10.0;
  tmp1 = -2.71 + (-784.58) * (-0.0033540164346805303 + DIVISION_SIM(1.0,273.15 + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* T_basin variable */),"273.15 + T_basin",equationIndexes));
  if(tmp0 < 0.0 && tmp1 != 0.0)
  {
    tmp3 = modf(tmp1, &tmp4);
    
    if(tmp3 > 0.5)
    {
      tmp3 -= 1.0;
      tmp4 += 1.0;
    }
    else if(tmp3 < -0.5)
    {
      tmp3 += 1.0;
      tmp4 -= 1.0;
    }
    
    if(fabs(tmp3) < 1e-10)
      tmp2 = pow(tmp0, tmp4);
    else
    {
      tmp6 = modf(1.0/tmp1, &tmp5);
      if(tmp6 > 0.5)
      {
        tmp6 -= 1.0;
        tmp5 += 1.0;
      }
      else if(tmp6 < -0.5)
      {
        tmp6 += 1.0;
        tmp5 -= 1.0;
      }
      if(fabs(tmp6) < 1e-10 && ((unsigned long)tmp5 & 1))
      {
        tmp2 = -pow(-tmp0, tmp3)*pow(tmp0, tmp4);
      }
      else
      {
        throwStreamPrint(threadData, "%s:%d: Invalid root: (%g)^(%g)", __FILE__, __LINE__, tmp0, tmp1);
      }
    }
  }
  else
  {
    tmp2 = pow(tmp0, tmp1);
  }
  if(isnan(tmp2) || isinf(tmp2))
  {
    throwStreamPrint(threadData, "%s:%d: Invalid root: (%g)^(%g)", __FILE__, __LINE__, tmp0, tmp1);
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[5]] /* S_sat variable */) = (60084.0) * (tmp2);
  threadData->lastEquationSolved = 17;
}

/*
equation index: 18
type: SIMPLE_ASSIGN
SR = c / S_sat
*/
void silica_eqFunction_18(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,18};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[4]] /* SR variable */) = DIVISION_SIM((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[0]] /* c STATE(1) */),(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[5]] /* S_sat variable */),"S_sat",equationIndexes);
  threadData->lastEquationSolved = 18;
}

/*
equation index: 19
type: SIMPLE_ASSIGN
excursion = SR - SR_setpoint
*/
void silica_eqFunction_19(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,19};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[10]] /* excursion variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[4]] /* SR variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* SR_setpoint PARAM */);
  threadData->lastEquationSolved = 19;
}

OMC_DISABLE_OPT
int silica_functionDAE(DATA *data, threadData_t *threadData)
{
  int equationIndexes[1] = {0};
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_DAE);
#endif

  data->simulationInfo->needToIterate = 0;
  data->simulationInfo->discreteCall = 1;
  silica_functionLocalKnownVars(data, threadData);
  static void (*const eqFunctions[9])(DATA*, threadData_t*) = {
    silica_eqFunction_11,
    silica_eqFunction_12,
    silica_eqFunction_13,
    silica_eqFunction_14,
    silica_eqFunction_15,
    silica_eqFunction_16,
    silica_eqFunction_17,
    silica_eqFunction_18,
    silica_eqFunction_19
  };
  
  for (int id = 0; id < 9; id++) {
    eqFunctions[id](data, threadData);
  }
  data->simulationInfo->discreteCall = 0;
  
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_DAE);
#endif
  return 0;
}


int silica_functionLocalKnownVars(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

/* forwarded equations */
extern void silica_eqFunction_13(DATA* data, threadData_t *threadData);

static void functionODE_system0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[1])(DATA*, threadData_t*) = {
    silica_eqFunction_13
  };
  
  if (data->simulationInfo->evalSelection) {
    for (int i = 0; i < data->simulationInfo->evalSelection->n; i++) {
      int id = data->simulationInfo->evalSelection->idx[i];
      eqFunctions[id](data, threadData);
    }
  } else {
    for (int id = 0; id < 1; id++) {
      eqFunctions[id](data, threadData);
    }
  }
}

int silica_functionODE(DATA *data, threadData_t *threadData)
{
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_FUNCTION_ODE);
#endif

  
  data->simulationInfo->callStatistics.functionODE++;
  
  silica_functionLocalKnownVars(data, threadData);
  functionODE_system0(data, threadData);

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_FUNCTION_ODE);
#endif

  return 0;
}

void silica_ODE_DAG(DATA* data, threadData_t* threadData)
{
  const size_t eqMap[] = {13};
  buildEvalDAG_ODE(data->modelData, sizeof(eqMap)/sizeof(size_t), eqMap);
}

/* forward the main in the simulation runtime */
extern int _main_SimulationRuntime(int argc, char **argv, DATA *data, threadData_t *threadData);
extern int _main_OptimizationRuntime(int argc, char **argv, DATA *data, threadData_t *threadData);

#include "silica_12jac.h"
#include "silica_13opt.h"

struct OpenModelicaGeneratedFunctionCallbacks silica_callback = {
  (int (*)(DATA *, threadData_t *, void *)) silica_performSimulation,    /* performSimulation */
  (int (*)(DATA *, threadData_t *, void *)) silica_performQSSSimulation,    /* performQSSSimulation */
  silica_updateContinuousSystem,    /* updateContinuousSystem */
  silica_callExternalObjectDestructors,    /* callExternalObjectDestructors */
  NULL,    /* initialNonLinearSystem */
  NULL,    /* initialLinearSystem */
  NULL,    /* initialMixedSystem */
  #if !defined(OMC_NO_STATESELECTION)
  silica_initializeStateSets,
  #else
  NULL,
  #endif    /* initializeStateSets */
  silica_initializeDAEmodeData,
  silica_ODE_DAG,
  silica_functionODE,
  silica_functionAlgebraics,
  silica_functionDAE,
  silica_functionLocalKnownVars,
  silica_input_function,
  silica_input_function_init,
  silica_input_function_updateStartValues,
  silica_data_function,
  silica_output_function,
  silica_setc_function,
  silica_setb_function,
  silica_function_storeDelayed,
  silica_function_storeSpatialDistribution,
  silica_function_initSpatialDistribution,
  silica_updateBoundVariableAttributes,
  silica_functionInitialEquations,
  GLOBAL_EQUIDISTANT_HOMOTOPY,
  NULL,
  silica_functionRemovedInitialEquations,
  silica_updateBoundParameters,
  silica_checkForAsserts,
  silica_function_ZeroCrossingsEquations,
  silica_function_ZeroCrossings,
  silica_function_updateRelations,
  silica_zeroCrossingDescription,
  silica_relationDescription,
  silica_function_initSample,
  silica_INDEX_JAC_A,
  silica_INDEX_JAC_ADJ,
  silica_INDEX_JAC_B,
  silica_INDEX_JAC_C,
  silica_INDEX_JAC_D,
  silica_INDEX_JAC_F,
  silica_INDEX_JAC_H,
  silica_initialAnalyticJacobianA,
  silica_initialAnalyticJacobianADJ,
  silica_initialAnalyticJacobianB,
  silica_initialAnalyticJacobianC,
  silica_initialAnalyticJacobianD,
  silica_initialAnalyticJacobianF,
  silica_initialAnalyticJacobianH,
  silica_functionJacA_column,
  silica_functionJacADJ_column,
  silica_functionJacB_column,
  silica_functionJacC_column,
  silica_functionJacD_column,
  silica_functionJacF_column,
  silica_functionJacH_column,
  silica_JacA_DAG,
  silica_linear_model_frame,
  silica_linear_model_datarecovery_frame,
  silica_mayer,
  silica_lagrange,
  silica_getInputVarIndicesInOptimization,
  silica_pickUpBoundsForInputsInOptimization,
  silica_setInputData,
  silica_getTimeGrid,
  silica_symbolicInlineSystem,
  silica_function_initSynchronous,
  silica_function_updateSynchronous,
  silica_function_equationsSynchronous,
  silica_inputNames,
  silica_dataReconciliationInputNames,
  silica_dataReconciliationUnmeasuredVariables,
  NULL,
  NULL,
  NULL,
  NULL,
  -1,
  NULL,
  NULL,
  -1

};

#define _OMC_LIT_RESOURCE_0_name_data "TowerSilicaDynamics"
#define _OMC_LIT_RESOURCE_0_dir_data "C:/Users/Nouman/Desktop/Furqan's Docs/Startup/mizan/modelica"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_0_name,19,_OMC_LIT_RESOURCE_0_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_0_dir,60,_OMC_LIT_RESOURCE_0_dir_data);

static const MMC_DEFSTRUCTLIT(_OMC_LIT_RESOURCES,2,MMC_ARRAY_TAG) {MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_0_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_0_dir)}};
void silica_setupDataStruc(DATA *data, threadData_t *threadData)
{
  assertStreamPrint(threadData,0!=data, "Error while initialize Data");
  threadData->localRoots[LOCAL_ROOT_SIMULATION_DATA] = data;
  data->callback = &silica_callback;
  OpenModelica_updateUriMapping(threadData, MMC_REFSTRUCTLIT(_OMC_LIT_RESOURCES));
  data->modelData->modelName = "TowerSilicaDynamics";
  data->modelData->modelFilePrefix = "silica";
  data->modelData->modelFileName = "TowerSilicaDynamics.mo";
  data->modelData->resultFileName = NULL;
  data->modelData->modelDir = "C:/Users/Nouman/Desktop/Furqan's Docs/Startup/mizan/modelica";
  data->modelData->modelGUID = "{dc888500-8e9b-4cd0-936d-112a44d1db4a}";
  #if defined(OPENMODELICA_XML_FROM_FILE_AT_RUNTIME)
  data->modelData->initXMLData = NULL;
  data->modelData->modelDataXml.infoXMLData = NULL;
  #else
  #if defined(_MSC_VER) /* handle joke compilers */
  {
  /* for MSVC we encode a string like char x[] = {'a', 'b', 'c', '\0'} */
  /* because the string constant limit is 65535 bytes */
  static const char contents_init[] =
    #include "silica_init.c"
    ;
  static const char contents_info[] =
    #include "silica_info.c"
    ;
    data->modelData->initXMLData = contents_init;
    data->modelData->modelDataXml.infoXMLData = contents_info;
  }
  #else /* handle real compilers */
  data->modelData->initXMLData =
  #include "silica_init.c"
    ;
  data->modelData->modelDataXml.infoXMLData =
  #include "silica_info.c"
    ;
  #endif /* defined(_MSC_VER) */
  #endif /* defined(OPENMODELICA_XML_FROM_FILE_AT_RUNTIME) */
  data->modelData->modelDataXml.fileName = "silica_info.json";
  data->modelData->resourcesDir = NULL;
  data->modelData->runTestsuite = 0;
  data->modelData->nStatesArray = 1;
  data->modelData->nDiscreteReal = 0;
  data->modelData->nVariablesRealArray = 11;
  data->modelData->nVariablesIntegerArray = 0;
  data->modelData->nVariablesBooleanArray = 0;
  data->modelData->nVariablesStringArray = 0;
  data->modelData->nParametersRealArray = 8;
  data->modelData->nParametersIntegerArray = 0;
  data->modelData->nParametersBooleanArray = 0;
  data->modelData->nParametersStringArray = 0;
  data->modelData->nParametersReal = 8;
  data->modelData->nParametersInteger = 0;
  data->modelData->nParametersBoolean = 0;
  data->modelData->nParametersString = 0;
  data->modelData->nAliasRealArray = 0;
  data->modelData->nAliasIntegerArray = 0;
  data->modelData->nAliasBooleanArray = 0;
  data->modelData->nAliasStringArray = 0;
  data->modelData->nInputVars = 0;
  data->modelData->nOutputVars = 0;
  data->modelData->nZeroCrossings = 0;
  data->modelData->nSamples = 0;
  data->modelData->nRelations = 0;
  data->modelData->nMathEvents = 0;
  data->modelData->nExtObjs = 0;
  data->modelData->modelDataXml.modelInfoXmlLength = 0;
  data->modelData->modelDataXml.nFunctions = 0;
  data->modelData->modelDataXml.nProfileBlocks = 0;
  data->modelData->modelDataXml.nEquations = 21;
  data->modelData->nMixedSystems = 0;
  data->modelData->nLinearSystems = 0;
  data->modelData->nNonLinearSystems = 0;
  data->modelData->nStateSets = 0;
  data->modelData->nJacobians = 7;
  data->modelData->nOptimizeConstraints = 0;
  data->modelData->nOptimizeFinalConstraints = 0;
  data->modelData->nDelayExpressions = 0;
  data->modelData->nBaseClocks = 0;
  data->modelData->nSpatialDistributions = 0;
  data->modelData->nSensitivityVars = 0;
  data->modelData->nSensitivityParamVars = 0;
  data->modelData->nSetcVars = 0;
  data->modelData->ndataReconVars = 0;
  data->modelData->nSetbVars = 0;
  data->modelData->nRelatedBoundaryConditions = 0;
  data->modelData->linearizationDumpLanguage = OMC_LINEARIZE_DUMP_LANGUAGE_MODELICA;
}

static int rml_execution_failed()
{
  fflush(NULL);
  fprintf(stderr, "Execution failed!\n");
  fflush(NULL);
  return 1;
}


#if defined(__MINGW32__) || defined(_MSC_VER)

#if !defined(_UNICODE)
#define _UNICODE
#endif
#if !defined(UNICODE)
#define UNICODE
#endif

#include <windows.h>
char** omc_fixWindowsArgv(int argc, wchar_t **wargv)
{
  char** newargv;
  /* Support for non-ASCII characters
  * Read the unicode command line arguments and translate it to char*
  */
  newargv = (char**)malloc(argc*sizeof(char*));
  for (int i = 0; i < argc; i++) {
    newargv[i] = omc_wchar_to_multibyte_str(wargv[i]);
  }
  return newargv;
}

#define OMC_MAIN wmain
#define OMC_CHAR wchar_t
#define OMC_EXPORT __declspec(dllexport) extern

#else
#define omc_fixWindowsArgv(N, A) (A)
#define OMC_MAIN main
#define OMC_CHAR char
#define OMC_EXPORT extern
#endif

#if defined(threadData)
#undef threadData
#endif
/* call the simulation runtime main from our main! */
#if defined(OMC_DLL_MAIN_DEFINE)
OMC_EXPORT int omcDllMain(int argc, OMC_CHAR **argv)
#else
int OMC_MAIN(int argc, OMC_CHAR** argv)
#endif
{
  char** newargv = omc_fixWindowsArgv(argc, argv);
  /*
    Set the error functions to be used for simulation.
    The default value for them is 'functions' version. Change it here to 'simulation' versions
  */
  omc_assert = omc_assert_simulation;
  omc_assert_withEquationIndexes = omc_assert_simulation_withEquationIndexes;

  omc_assert_warning_withEquationIndexes = omc_assert_warning_simulation_withEquationIndexes;
  omc_assert_warning = omc_assert_warning_simulation;
  omc_terminate = omc_terminate_simulation;
  omc_throw = omc_throw_simulation;

  int res;
  DATA data;
  MODEL_DATA modelData;
  SIMULATION_INFO simInfo;
  data.modelData = &modelData;
  data.simulationInfo = &simInfo;
  measure_time_flag = 0;
  compiledInDAEMode = 0;
  compiledWithSymSolver = 0;
  MMC_INIT(0);
  omc_alloc_interface.init();
  {
    MMC_TRY_TOP()
  
    MMC_TRY_STACK()
  
    silica_setupDataStruc(&data, threadData);
    res = _main_initRuntimeAndSimulation(argc, newargv, &data, threadData);
    if(res == 0) {
      if (omc_flag[FLAG_MOO_OPTIMIZATION]) {
        res = _main_OptimizationRuntime(argc, newargv, &data, threadData);
      } else {
        res = _main_SimulationRuntime(argc, newargv, &data, threadData);
      }
    }
    
    MMC_ELSE()
    rml_execution_failed();
    fprintf(stderr, "Stack overflow detected and was not caught.\nSend us a bug report at https://trac.openmodelica.org/OpenModelica/newticket\n    Include the following trace:\n");
    printStacktraceMessages();
    fflush(NULL);
    return 1;
    MMC_CATCH_STACK()
    
    MMC_CATCH_TOP(return rml_execution_failed());
  }

  fflush(NULL);
  return res;
}

#ifdef __cplusplus
}
#endif


