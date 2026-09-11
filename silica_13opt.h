#if defined(__cplusplus)
  extern "C" {
#endif
  int silica_mayer(DATA* data, modelica_real** res, short*);
  int silica_lagrange(DATA* data, modelica_real** res, short *, short *);
  int silica_getInputVarIndicesInOptimization(DATA* data, int* input_var_indices);
  int silica_pickUpBoundsForInputsInOptimization(DATA* data, modelica_real* min, modelica_real* max, modelica_real*nominal, modelica_boolean *useNominal, char ** name, modelica_real * start, modelica_real * startTimeOpt);
  int silica_setInputData(DATA *data, const modelica_boolean file);
  int silica_getTimeGrid(DATA *data, modelica_integer * nsi, modelica_real**t);
#if defined(__cplusplus)
}
#endif
