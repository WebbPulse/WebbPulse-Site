# WebbPulse-Site

The WebbPulse company site, served at [webbpulse.com](https://webbpulse.com).

- `site/` is a static React and Vite site, prerendered at build time.
- `terraform/` holds its hosting: a `spa-frontend` distribution and bucket, the
  ACM certificate, the apex and `www` records, and the GitHub Actions roles. It
  runs on the WebbPulse Terraform plane in the Portfolio AWS accounts, as the
  WebbPulse-Site and WebbPulse-Site-staging workspaces.
- Production serves `webbpulse.com` and `www.webbpulse.com`. Staging serves
  `staging.webbpulse.com` and `www.staging.webbpulse.com` from its own child
  zone, behind the staging access gate.
- The viewer-request handler in `terraform/company_site_functions/` sends `www`
  to the apex, sends the old portfolio paths (`/blog`, `/privacy`) with a 301 to
  `portfolio.webbpulse.com`, serves `/` and files with an extension from the
  bucket, and answers any other path with a 404 page.

Changes go through a pull request into `staging`, then a promotion pull request
from a `promote/<date>` branch into `main`. A push to either branch deploys.

The site moved here from WebbPulse-Portfolio, where its earlier history lives.
