/* Algebraic */
#include "silica_model.h"

#ifdef __cplusplus
extern "C" {
#endif

/* forwarded equations */
extern void silica_eqFunction_11(DATA* data, threadData_t *threadData);
extern void silica_eqFunction_12(DATA* data, threadData_t *threadData);
extern void silica_eqFunction_14(DATA* data, threadData_t *threadData);
extern void silica_eqFunction_15(DATA* data, threadData_t *threadData);
extern void silica_eqFunction_16(DATA* data, threadData_t *threadData);
extern void silica_eqFunction_17(DATA* data, threadData_t *threadData);
extern void silica_eqFunction_18(DATA* data, threadData_t *threadData);
extern void silica_eqFunction_19(DATA* data, threadData_t *threadData);

static void functionAlg_system0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[8])(DATA*, threadData_t*) = {
    silica_eqFunction_11,
    silica_eqFunction_12,
    silica_eqFunction_14,
    silica_eqFunction_15,
    silica_eqFunction_16,
    silica_eqFunction_17,
    silica_eqFunction_18,
    silica_eqFunction_19
  };
  
  if (data->simulationInfo->evalSelection) {
    for (int i = 0; i < data->simulationInfo->evalSelection->n; i++) {
      int id = data->simulationInfo->evalSelection->idx[i];
      eqFunctions[id](data, threadData);
    }
  } else {
    for (int id = 0; id < 8; id++) {
      eqFunctions[id](data, threadData);
    }
  }
}
/* for continuous time variables */
int silica_functionAlgebraics(DATA *data, threadData_t *threadData)
{

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_ALGEBRAICS);
#endif
  data->simulationInfo->callStatistics.functionAlgebraics++;

  silica_function_savePreSynchronous(data, threadData);
  
  functionAlg_system0(data, threadData);

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_ALGEBRAICS);
#endif

  return 0;
}

#ifdef __cplusplus
}
#endif
