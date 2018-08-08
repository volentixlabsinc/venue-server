import { basicInstance } from './workflows/basic.js';

export default {
  thresholds: Object.assign(
    {},
    basicInstance.threshold
  ),
  vus: 1,
  iterations: 10,
  noUsageReport: true,
};