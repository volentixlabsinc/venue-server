import { basicInstance } from './workflows/basic.js';

export default {
  thresholds: Object.assign(
    {},
    basicInstance.threshold
  ),
  vus: 1,
  stages: [
    { duration: "30s", target: 3 }
  ],
  noUsageReport: true,
};