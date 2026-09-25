# Audit deferred response validation

Trace an ordinary `DataRequest` from `Session.request` through adaptation, task
completion, deferred `DataRequest.validate` callbacks, retry selection, and
response serialization in `/app/src/alamofire`. Distinguish preflight URL-request
validation from response validation, and a stored closure from a direct call.
This is a read-only source audit; do not contact a server or change the library.

Write `/app/src/deferred-validation.json` with exactly two objects, `locations`
and `decisions`. Each location is exactly `{"file":"alamofire/Source/...swift",
"symbol":"Type.member"}`. Use the declaring type, including for extensions;
omit parameter lists, generic arguments, and line numbers. Overloads share the
same symbol spelling. Name the enclosing member for its nested closures.

## Locations

| Key | Responsibility |
| --- | --- |
| `request_factory` | Session overload constructing a `DataRequest` from a `URLRequestConvertible`. |
| `typed_dispatch` | Dispatch a generic request to upload/data/download/stream setup according to its concrete type. |
| `initial_adaptation` | Convert and validate the initial URL request, invoke its adapter, and validate the adapted result. |
| `task_creation` | Ask the request for a URLSession task and associate the task with its request. |
| `data_task_factory` | Data-request override constructing the actual URLSession data task. |
| `completion_delegate` | URLSession delegate callback forwarding task completion through the session state provider. |
| `completion_barrier` | Session member either invoking completion or storing it until metrics have arrived. |
| `metrics_release` | Session member releasing a stored completion when task metrics arrive. |
| `metrics_state` | Request/task map member marking completion and deciding whether disassociation is possible. |
| `validator_registration` | Data-request member wrapping a custom validation closure and appending it to the shared collection. |
| `validator_execution` | Base request member invoking the registered validation closures after task completion. |
| `default_validation` | Extension member composing the default status-code and content-type validators. |
| `retry_entry` | Base request member choosing retry versus finish after validation. |
| `retry_composition` | Session member composing request-specific and session-level retriers. |
| `adapter_chain` | Interceptor member advancing the ordered adapter chain after a successful adaptation. |
| `serialization_start` | Base request member marking finishing and starting response serializers. |
| `response_serialization` | Data-request member passing the current request/response/data/error to a generic response serializer. |
| `preflight` | URL-request extension member rejecting an invalid GET request body before transport. |

## Decisions

Except the three array entries below, use JSON booleans. Assume a normal
non-cancelled data request, successful conversion/adaptation unless a question
states otherwise, and no custom hooks beyond those named. Register response
validators before completion. Do not confuse `DataStreamRequest` or
`DownloadRequest` overloads with the data-request flow.

| Key | Question |
| --- | --- |
| `task_created_synchronously_by_public_request` | Does the public factory build the URLSession task synchronously, before returning the `DataRequest`, rather than scheduling setup? |
| `modifier_before_parameter_encoding` | In the dictionary-parameter request-convertible path, is the request modifier applied before parameter encoding? |
| `initial_and_adapted_requests_validated` | Are both the original URL request and a successful adapted result subjected to preflight validation? |
| `adapter_order` | Array: list `request_interceptor` and `session_interceptor` in their execution order when both are present and succeed. |
| `adapter_failure_runs_remaining` | Does a failing adapter still advance the remaining adapter chain? |
| `bare_request_automatically_validates_404` | Without calling a response-validation API, does creating a request automatically install a validator that rejects HTTP 404? |
| `custom_validator_runs_at_registration` | Does registering a custom response-validation closure immediately execute that closure? |
| `validators_run_on_serialization_queue` | Are deferred validation closures dispatched to the response-serialization queue rather than executed on the request's underlying queue? |
| `validator_callbacks_invoked_under_collection_lock` | Does the base request hold the `Protected` collection's lock while invoking the validation callbacks? |
| `existing_error_preserved_at_completion` | If the request already has an error, does task completion preserve it instead of replacing it with the new task error? |
| `custom_validators_after_first_failure_run` | After the first custom validator records a failure, do subsequent registered custom validation bodies still run? |
| `default_validator_order` | Array of `status_code` and `content_type`, in registration order. |
| `default_status_bounds` | Two-integer array containing the inclusive lowest and highest default acceptable status codes. |
| `absent_accept_uses_any_mime` | With no Accept header, does default content validation permit any MIME type? |
| `empty_body_skips_content_type_check` | For a data response with empty or absent data, is the content-type check successful even when MIME information is missing or unacceptable? |
| `wildcard_allows_missing_mime` | With nonempty data and no response MIME type, does an acceptable `*/*` entry permit validation? |
| `custom_error_wrapped_as_validation_failure` | Is a failed custom validator's non-AFError wrapped as an AFError response-validation failure? |
| `validation_failure_eligible_for_retry` | With a delegate and no cancellation, can a response-validation failure be passed to retry selection? |
| `validators_retained_on_retry` | Does the standard data-request retry reset retain the registered validators for the next attempt? |
| `darwin_completion_before_metrics_waits` | On macOS 13 without FoundationNetworking, if task completion arrives before metrics, does the session defer forwarding completion until metrics arrive? |
| `foundationnetworking_completion_waits_for_metrics` | In the FoundationNetworking compilation branch, does completion wait for metrics before disassociating the task? |
| `serializer_receives_validation_error` | Does the generic response serializer receive the request's current validation error through its `error` argument? |
| `preflight_rejects_get_body` | Does preflight validation reject a GET request whose `httpBody` is non-nil, even if the Data is empty? |

Grade is complete source-backed correctness, independent of tool use. Preserve
`src/alamofire`. Scratch files elsewhere are allowed. The fixture is source for
inspection, not a complete Swift/Xcode build. No network, compiler, or service
installation is needed to solve the task.
