# Audit mutation-to-canvas invalidation

The frozen Excalidraw source is in `/app/src/excalidraw`. Trace how a changed
element reaches the static canvas, from `mutateElement` through the scene's
observer registration and React to `renderStaticScene`. Also distinguish
element mutation, render notification, memoization, and frame scheduling.
Read the implementation; do not assume that an observer is an ordinary direct
call or that suppressing notification suppresses the mutation itself.

Write `/app/src/render-invalidation.json` with exactly two objects, `locations`
and `decisions`. Do not change the frozen source. No installation, browser,
network, or live service is needed. Any navigation method is acceptable.

## Locations

Each entry is exactly `{"file": "excalidraw/...", "symbol": "..."}`. Paths are
relative to `/app/src`, case-sensitive. Use `Class.method` for class members
(including arrow-function fields), and the declared name for free functions.
For callbacks nested inside a named function/member, name that enclosing
function/member, not the anonymous callback. Do not include line numbers.

Find the implementation owning each responsibility:

| Key | Responsibility |
| --- | --- |
| `mutation_gate` | Decide whether an in-place element update actually changed anything. |
| `scene_dispatch` | Refresh the scene nonce and invoke registered scene callbacks. |
| `observer_registration` | Register the application render callback with its scene during mounting. |
| `react_handoff` | Implement the application's render trigger, including its force branch. |
| `render_selection` | During application rendering, obtain the renderable/visible element collections. |
| `renderable_cache` | Class member wrapping renderable-element computation in memoization, with the scene nonce among its inputs. |
| `static_memo` | Compare old/new static-canvas props to decide whether React can skip rendering. |
| `canvas_effect` | Component whose effect synchronizes canvas dimensions and calls the static-scene renderer. |
| `static_dispatch` | Public static-scene rendering function choosing immediate versus throttled work. |
| `frame_coalescing` | Shared animation-frame utility implementing pending and trailing calls. |
| `paint` | Internal static-scene function painting the visible elements and their bound text. |
| `shape_generation` | Class member obtaining or generating cached rough shapes. |
| `cache_cleanup` | Renderer member cancelling queued rendering and clearing its memoized computation. |

## Decisions

Use JSON booleans for every key except the three explicitly typed entries below.
For mutation questions, use an existing, scene-mapped ordinary rectangle; changed
values differ from the old values, there are no unrelated updates or exceptions,
and no other caller performs notification on its behalf.

| Key | Question |
| --- | --- |
| `no_op_notifies` | Does a mutation containing only an unchanged primitive field notify scene listeners? |
| `suppressed_notification_bumps_version` | Does changing width with `informMutation=false` still increment the element version? |
| `suppressed_notification_invalidates_shape` | Does that same suppressed-notification width change invalidate the cached shape? |
| `x_only_invalidates_shape` | Does changing only `x` explicitly delete the element's shape cache entry in `mutateElement`? |
| `listener_added_during_dispatch_runs_now` | If the first listener adds a new listener during a dispatch, does the new listener run in that same dispatch? |
| `listener_removed_during_dispatch_still_runs` | If the first listener removes a later registered listener during a dispatch, is that later listener still invoked in the current dispatch? |
| `duplicate_registration_throws` | Does registering the identical scene callback twice throw? |
| `scene_to_app_handoff` | String: `direct_method_call`, `registered_callback`, or `event_name_lookup` for the scene-to-application render handoff. |
| `app_to_render_handoff` | String: `direct_method_call`, `react_state_update`, or `animation_frame_callback` for the normal application-trigger-to-React-render handoff. |
| `default_app_callback_notifies_scene_again` | Does the no-argument application callback invoked by the scene immediately ask the scene to dispatch again? |
| `force_render_regenerates_scene_nonce` | Does explicitly invoking the application's force-render branch refresh the scene nonce? |
| `changed_nonce_invalidates_renderer_cache` | With all other memoization inputs unchanged, does a changed scene nonce cause renderable-element computation to run again? |
| `changed_nonce_skips_static_canvas` | With other props unchanged, does the static-canvas comparator permit skipping when the scene nonce differs? |
| `unchanged_dimensions_reset_canvas` | Does the canvas effect unconditionally assign canvas width/height even when their computed values have not changed? |
| `render_throttling_default` | Is render throttling enabled when its window flag is absent? |
| `react17_flag_enables_throttling` | With React 17 and the window flag explicitly true, does the throttling policy enable it? |
| `react18_flag_enables_throttling` | With React 18 and that flag explicitly true, does the policy enable it? |
| `raf_three_queued_arguments` | Array of strings: in production mode, call a fresh `throttleRAF(fn, {trailing: true})` wrapper synchronously with `"first"`, `"second"`, `"third"` before any animation frame. List the arguments eventually passed to `fn`, in order, after all scheduled frames finish. No flush, cancel, recursion, or further calls occur. |
| `export_reuses_shape` | Does shape generation reuse an existing cached shape when `isExporting=true`? |
| `null_shape_is_cache_hit` | Outside export, is a cached `null` shape treated as a valid cached result? |
| `shape_generation_clears_element_canvas_cache` | When a shape must actually be generated, is the separate element-canvas cache entry cleared? |
| `new_element_painted_on_static_canvas` | Is the element matching `newElementId` included in the renderer's ordinary static-canvas element collection? |
| `bound_text_painted_with_container` | If an ordinary rectangle container and its bound text are both visible and present in the renderable map, does the static painter render that text with the container rather than painting it independently twice? |

The artifact is graded for complete source-backed correctness, independently of
tool use. This is a static audit of the pinned implementation, not a request to
change rendering behavior or prove browser scheduling beyond the stated scenario.
