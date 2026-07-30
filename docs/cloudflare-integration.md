# Cloudflare Integration

Press can manage Cloudflare DNS, remotely managed Tunnels, Access-protected SSH,
Cloudflare for SaaS custom hostnames, and Registrar domain discovery from one
encrypted `Cloudflare Settings` record.

## Initial setup

1. Create a scoped Cloudflare API token with account read, tunnel edit, Access
   application/policy edit, Access service-token edit, zone read, DNS edit, and
   SSL/custom-hostname edit permissions. Add Registrar edit only when domain
   registration is required.
2. Open `Cloudflare Settings`, enter the token and account ID, and select the
   managed features.
3. Use **Test Connection**, then **Import Zone** for every zone Press will
   manage.
4. For Cloudflare for SaaS, enable it on the imported Root Domain, set a proxied
   fallback-origin hostname and a friendly CNAME target, then run
   **Configure SaaS Routing**.

The Press controller must have the `cloudflared` CLI in its `PATH`; Press uses
that local binary as the SSH proxy after a server tunnel becomes healthy.

The API token and Access service-token secret are stored in Frappe Password
fields. Tunnel tokens are passed to Ansible as masked variables and written on
the target server with mode `0600`.

## Server setup

Select **Behind Cloudflare** and a Cloudflare Root Domain when creating a
self-hosted server. Press creates one tunnel per application, database, or proxy
server and installs `cloudflared` as an enabled systemd service with automatic
restart.

The existing public IP is used only for initial SSH bootstrap. If the host has
no inbound bootstrap path, use **Show Bootstrap Command** and run the generated
one-time command through the provider console or cloud-init. Cloudflare cannot
install software on a host until that host has either an existing management
path or a preinstalled bootstrap agent.

After Cloudflare reports the tunnel as healthy, Press Ansible jobs connect to
the generated SSH hostname through `cloudflared access ssh`. Access policy is
scoped to that SSH hostname and does not protect or interrupt the tunnel's HTTP
routes.

## Lifecycle

- Hourly reconciliation restores tunnel configuration and DNS drift and
  refreshes tunnel, custom-hostname, and certificate status.
- Archiving a server revokes its Access application, DNS routes, active tunnel
  connections, and tunnel before the server can be marked archived.
- Rotating the shared Access service token immediately updates the encrypted
  credential Press uses for subsequent SSH connections.
- Site Domain records show Cloudflare ownership and certificate validation
  records, status, last refresh time, and the last integration error.

Cloudflare Registrar search results are advisory. Press performs an
authoritative availability and price check immediately before registration and
requires confirmation of the exact current charge. Registrar POST requests are
never automatically retried.
