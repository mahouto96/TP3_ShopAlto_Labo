import http from 'k6/http';
import { sleep, check } from 'k6';
export const options = {
  stages: [
    { duration: '20s', target: 10 },
    { duration: '30s', target: 30 },
    { duration: '20s', target: 0 },
  ],
  thresholds: { http_req_failed: ['rate<0.02'], http_req_duration: ['p(95)<800'] },
};
export default function () {
  const res = http.get('http://haproxy/catalog');
  check(res, {'status 200': r => r.status === 200});
  sleep(0.2);
}
