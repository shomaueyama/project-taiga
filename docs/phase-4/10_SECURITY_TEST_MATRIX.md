# Security Test Matrix

| Area | Test | Expected Result | Coverage |
|---|---|---|---|
| HTTP headers | Health response includes hardening headers | Headers present | `test_security_headers_and_untrusted_cors_origin` |
| CORS | Preflight from untrusted origin | No allow-origin header | `test_security_headers_and_untrusted_cors_origin` |
| Authentication | Protected mutations without auth | HTTP 401 | `test_protected_mutations_reject_missing_authentication` |
| IDOR | Learner reads another learner assignment | HTTP 404 | `test_learner_idor_and_role_escalation_are_denied` |
| IDOR | Learner reads another learner submission | HTTP 404 | `test_learner_idor_and_role_escalation_are_denied` |
| Authorization | Learner creates review | HTTP 403 | `test_learner_idor_and_role_escalation_are_denied` |
| Authorization | Reviewer performs admin mutation | HTTP 403 | `test_learner_idor_and_role_escalation_are_denied` |
| Input validation | Extra request field | HTTP 422 | `test_input_validation_rejects_extra_fields_malformed_json_and_rate_limits` |
| Input validation | Malformed JSON | HTTP 422 and no traceback | `test_input_validation_rejects_extra_fields_malformed_json_and_rate_limits` |
| Rate limit | Exceed configured window | HTTP 429 | `test_input_validation_rejects_extra_fields_malformed_json_and_rate_limits` |
| Upload | Absolute path | Rejected upload record | `test_upload_security_rejects_unsafe_inputs_and_uses_generated_storage_key` |
| Upload | Empty file | Rejected upload record | `test_upload_security_rejects_unsafe_inputs_and_uses_generated_storage_key` |
| Upload | MIME mismatch | Rejected upload record | `test_upload_security_rejects_unsafe_inputs_and_uses_generated_storage_key` |
| Upload | Double extension executable | Rejected upload record | `test_upload_security_rejects_unsafe_inputs_and_uses_generated_storage_key` |
| Upload storage | Original filename in storage key | Not present | `test_upload_security_rejects_unsafe_inputs_and_uses_generated_storage_key` |
| Runner | Shell metacharacter payload | HTTP 409 and no job | `test_runner_rejects_unsafe_payloads_and_worker_bounds_poison_messages` |
| Worker | Poison runner outbox event | Not published as trusted result | `test_runner_rejects_unsafe_payloads_and_worker_bounds_poison_messages` |
| Config | Invalid security boolean | Validation error | `test_security_sensitive_flags_fail_closed` |
