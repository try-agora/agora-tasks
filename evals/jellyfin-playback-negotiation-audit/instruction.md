# Audit playback negotiation across Jellyfin's request and media layers

Before changing playback policy, trace `POST Items/{itemId}/PlaybackInfo` through
the frozen Jellyfin 10.10.7 source in `/app/src/jellyfin`. Follow user selection,
device capabilities, provider dispatch, bitrate limits, and video stream choice.
This is a read-only source audit; do not implement a repair or start a server.

The main navigation endpoints are `MediaInfoController.GetPostedPlaybackInfo`
and `StreamBuilder.BuildVideoItem`. Audit how the request reaches that candidate
builder and the related provider/policy branches listed below, rather than just
finding those two declarations.

Write `/app/src/playback-negotiation.json` containing exactly `locations` and
`decisions`. Each location is `{"file":"jellyfin/path/File.cs",
"symbol":"Class.Method","line":42}`. Paths are relative to `/app/src`;
omit namespaces and parameter lists. Give the first line of the decisive
expression, not the method declaration. Overloaded methods share the same symbol
spelling; the expression and line disambiguate them.

Include these location keys:

| Key | Decisive expression |
| --- | --- |
| `user_claim` | Claims extension fetches the authenticated user-ID claim. |
| `user_boundary` | Request helper tests whether a different requested user is forbidden for a non-administrator. |
| `device_profile` | POST handler fetches stored capabilities when no profile was posted. |
| `manager_binding` | Application host registers the concrete media-source manager for its interface. |
| `provider_registration` | Application host supplies exported media-source providers to that manager. |
| `source_fetch` | Playback-info helper requests playback sources when no live-stream ID was supplied. |
| `provider_fanout` | Manager awaits the collection of dynamic-provider tasks together. |
| `provider_dispatch` | Manager invokes an individual provider's media-source method. |
| `channel_branch` | Channel provider chooses whether this item's source type is a channel. |
| `source_copy` | Playback-info helper makes a deep JSON copy before device-specific mutations. |
| `remote_cap` | Helper clamps the client bitrate against the effective remote-user limit. |
| `stream_dispatch` | Helper's audio-versus-video conditional chooses the optimal-stream builder. |
| `video_candidate` | Video-stream selector calls the per-source candidate builder; identify this call, not the allocation inside the candidate builder. |
| `video_eligibility` | Candidate builder computes initial direct-play eligibility from enable/force/bitrate flags. |
| `streaming_default` | Options resolve the profile's streaming bitrate when no explicit bitrate overrides it. |
| `response_order` | Playback-info helper starts ordering the response's media sources. |
| `auto_open_guard` | POST handler tests source existence, opening requirement, and absence of an existing live-stream ID before opening it. |

Derive these `decisions` from this implementation:

- `query_overrides_body`: boolean, for a non-null query bitrate and a different
  posted bitrate.
- `missing_profile_uses_device_capabilities`: boolean, when capabilities exist.
- `source_filter_case_sensitive`: boolean, for a specified media-source ID in
  the playback-info helper, with no live-stream ID.
- `auto_open_selection_case_sensitive`: boolean, for the POST handler's later
  selection of a specified media-source ID.
- `providers_awaited_together`: boolean, rather than serially awaiting each one.
- `provider_exception_result`: `empty_sources` or `propagated_exception`, for
  an ordinary exception thrown by one dynamic provider.
- `device_mutations_touch_manager_objects`: boolean, after a successful source
  clone in the playback-info helper.
- `remote_effective_bitrate`: integer, when the client requests 12000000, the
  user's remote limit is 8000000, the server's is 4000000, and the client is
  outside the local network.
- `local_effective_bitrate`: integer, same limits but inside the local network.
- `force_direct_play_bypasses_bitrate_gate`: boolean, in the candidate builder's
  initial eligibility expression when direct play is enabled. This does not
  imply bypassing later codec/container checks or the DVD/Blu-ray exception.
- `video_copy_disabled_clears_direct_stream`: boolean, at the helper's initial
  source capability gate when `allowVideoStreamCopy` is false.
- `auto_open_default`: boolean, when neither query nor body supplies a value.
- `non_channel_provider_result`: `empty_sources` or `channel_sources`, for the
  channel provider when the item is not from a channel.
- `no_sources_error`: the unqualified playback-error enum member used when the
  playback-info helper has no media sources.

Assume normal successful dependencies except the explicit provider-exception
question. Do not modify `src/jellyfin`. Scratch files elsewhere in `/app` are
allowed. The fixture contains production C# source and project metadata, not a
complete build distribution. No .NET installation or network access is needed.
