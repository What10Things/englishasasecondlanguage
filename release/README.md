# Production source bundle

The complete readable source is stored as a compressed release bundle split into GitHub-safe text parts.

To reconstruct it locally:

```bash
cat release/site-bundle.part* | base64 -d > /tmp/efl-site-bundle.tar.gz
tar -xzf /tmp/efl-site-bundle.tar.gz
```

The deployment workflow performs these steps automatically before linting, testing and uploading the `godaddy/` directory.
