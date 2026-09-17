# YasinCoder Post-release TODO

Completed roadmap items are tracked by their merged GitHub Issues and are intentionally not duplicated here.

## Current release work

- Publish the first tagged release after the release gates are verified.
- Run a clean-clone end-to-end provider-backed chat verification with a disposable/mock provider.
- Perform manual validation of the Cloudflare Worker against a real configured upstream.

## Future enhancements

- Distributed Cloudflare rate limiting with a Durable Object or Cloudflare-native rate limiting product.
- Additional provider adapters and provider-specific discovery improvements.
- Expanded sandbox resource controls where platform support permits.
- Broader platform-specific integration tests.
