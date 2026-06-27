# Entra Hosted Provisioning Runbook

## Correction

For 1Password automated provisioning with Microsoft Entra ID, the documented lane is SCIM URL + bearer token.

OAuth setup or callback instructions for Entra provisioning are:

```text
DATA NOT IN SOURCES: REQUIRES EXTERNAL DOCUMENTATION
```

Do not configure SCIM provisioning as if it were an OIDC callback flow.

## Hosted Provisioning Flow

### In 1Password

1. Sign in to the 1Password account.
2. Go to `Integrations`.
3. Select `Automated User Provisioning`.
4. Select `Switch to hosted provisioning`.
5. Select `Start setup`.
6. Select `Set up hosted provisioning`.
7. Save generated credentials in 1Password.
8. Keep the setup page open while updating Entra.

### In Microsoft Entra ID

1. Open Microsoft Entra admin center.
2. Go to `Enterprise applications`.
3. Select the `1Password EPM` application.
4. Select `Provisioning`.
5. Open `Admin Credentials`.
6. Tenant URL: paste the SCIM URL from the 1Password hosted provisioning setup page.
   - Official example: `https://provisioning.1password.com/scim/v2`
   - Do not include a trailing slash.
7. Secret token: paste the bearer token from the 1Password hosted provisioning setup page.
8. Select `Test Connection`.
9. Select `Save`.
10. Return to the 1Password hosted provisioning setup tab.
11. Select `Save credentials in 1Password`.
12. Select `Done`.

## First-Time Self-Hosted SCIM Bridge Flow

This lane still exists in support documentation, but 1Password says hosted automated provisioning is preferred for Entra ID and Okta.

1. Set up and deploy 1Password SCIM Bridge.
2. Ensure the Entra administrator has a premium subscription.
3. Turn on `Provisioning users & groups` in the 1Password Automated User Provisioning page.
4. In Entra, create a non-gallery enterprise application named `1Password EPM`.
5. Add a test user or group.
6. Go to `Provisioning`.
7. Select `Connect your application`.
8. Tenant URL: SCIM bridge URL, not the 1Password sign-in URL.
   - Official example: `https://scim.example.com`
9. Secret token: bearer token for the SCIM bridge.
10. Select `Test Connection`, then `Create`.
11. Configure attribute mappings.
12. Change `userName` from `userPrincipalName` to `mail`, or another routable email attribute.
13. Test with `Provision on demand`.
14. Add target users/groups.
15. Start provisioning.

## Known Constraints

- Entra ID has a documented 40-minute sync cycle.
- 1Password says self-hosted SCIM Bridge will be deprecated in the future.
- User management with 1Password CLI is not supported while automated provisioning is turned on.
- Groups with account-wide cryptographic permissions are not automatically managed by hosted provisioning.

