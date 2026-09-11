/* Initialization */
#include "silica_model.h"
#include "silica_11mix.h"
#include "silica_12jac.h"
#if defined(__cplusplus)
extern "C" {
#endif

void silica_functionInitialEquations_0(DATA *data, threadData_t *threadData);

/*
equation index: 1
type: SIMPLE_ASSIGN
S_sat_mean = 60084.0 * 10.0 ^ (-2.71 + (-784.58) * (-0.0033540164346805303 + 1.0 / (273.15 + T_mean)))
*/
void silica_eqFunction_1(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,1};
  modelica_real tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  modelica_real tmp3;
  modelica_real tmp4;
  modelica_real tmp5;
  modelica_real tmp6;
  tmp0 = 10.0;
  tmp1 = -2.71 + (-784.58) * (-0.0033540164346805303 + DIVISION_SIM(1.0,273.15 + (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[4]] /* T_mean PARAM */),"273.15 + T_mean",equationIndexes));
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
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* S_sat_mean variable */) = (60084.0) * (tmp2);
  threadData->lastEquationSolved = 1;
}

/*
equation index: 2
type: SIMPLE_ASSIGN
T_basin = T_mean - T_amp * cos(7.27220521664304e-5 * (time - t_peak))
*/
void silica_eqFunction_2(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,2};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* T_basin variable */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[4]] /* T_mean PARAM */) - (((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[3]] /* T_amp PARAM */)) * (cos((7.27220521664304e-5) * (data->localData[0]->timeValue - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[7]] /* t_peak PARAM */)))));
  threadData->lastEquationSolved = 2;
}
extern void silica_eqFunction_17(DATA *data, threadData_t *threadData);

extern void silica_eqFunction_11(DATA *data, threadData_t *threadData);

extern void silica_eqFunction_12(DATA *data, threadData_t *threadData);


/*
equation index: 6
type: SIMPLE_ASSIGN
c = $START.c
*/
void silica_eqFunction_6(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,6};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[0]] /* c STATE(1) */) = ((modelica_real *)((data->modelData->realVarsData[0] /* c STATE(1) */).attribute .start.data))[0];
  threadData->lastEquationSolved = 6;
}
extern void silica_eqFunction_14(DATA *data, threadData_t *threadData);

extern void silica_eqFunction_18(DATA *data, threadData_t *threadData);

extern void silica_eqFunction_19(DATA *data, threadData_t *threadData);

extern void silica_eqFunction_13(DATA *data, threadData_t *threadData);

OMC_DISABLE_OPT
void silica_functionInitialEquations_0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[10])(DATA*, threadData_t*) = {
    silica_eqFunction_1,
    silica_eqFunction_2,
    silica_eqFunction_17,
    silica_eqFunction_11,
    silica_eqFunction_12,
    silica_eqFunction_6,
    silica_eqFunction_14,
    silica_eqFunction_18,
    silica_eqFunction_19,
    silica_eqFunction_13
  };
  
  for (int id = 0; id < 10; id++) {
    eqFunctions[id](data, threadData);
  }
}

int silica_functionInitialEquations(DATA *data, threadData_t *threadData)
{
  data->simulationInfo->discreteCall = 1;
  silica_functionInitialEquations_0(data, threadData);
  data->simulationInfo->discreteCall = 0;
  
  return 0;
}

/* No silica_functionInitialEquations_lambda0 function */

int silica_functionRemovedInitialEquations(DATA *data, threadData_t *threadData)
{
  const int *equationIndexes = NULL;
  double res = 0.0;

  
  return 0;
}


#if defined(__cplusplus)
}
#endif
