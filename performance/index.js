import { group } from 'k6';
import options from './globalOptions.js';
import basic from './workflows/basic.js';

export { options };

export default () => {
  group('API_1 Tests', () => {
    basic();
  });
};