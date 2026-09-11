/* update bound parameters and variable attributes (start, nominal, min, max) */
#include "silica_model.h"
#if defined(__cplusplus)
extern "C" {
#endif

OMC_DISABLE_OPT
int silica_updateBoundVariableAttributes(DATA *data, threadData_t *threadData)
{
  /* min ******************************************************** */
  infoStreamPrint(OMC_LOG_INIT, 1, "updating min-values");
  messageClose(OMC_LOG_INIT);
  
  /* max ******************************************************** */
  infoStreamPrint(OMC_LOG_INIT, 1, "updating max-values");
  messageClose(OMC_LOG_INIT);
  
  /* nominal **************************************************** */
  infoStreamPrint(OMC_LOG_INIT, 1, "updating nominal-values");
  messageClose(OMC_LOG_INIT);
  
  /* start ****************************************************** */
  infoStreamPrint(OMC_LOG_INIT, 1, "updating primary start-values");
  messageClose(OMC_LOG_INIT);
  
  return 0;
}

void silica_updateBoundParameters_0(DATA *data, threadData_t *threadData);
extern void silica_eqFunction_1(DATA *data, threadData_t *threadData);

OMC_DISABLE_OPT
void silica_updateBoundParameters_0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[1])(DATA*, threadData_t*) = {
    silica_eqFunction_1
  };
  
  for (int id = 0; id < 1; id++) {
    eqFunctions[id](data, threadData);
  }
}
OMC_DISABLE_OPT
int silica_updateBoundParameters(DATA *data, threadData_t *threadData)
{
  silica_updateBoundParameters_0(data, threadData);
  return 0;
}

#if defined(__cplusplus)
}
#endif
