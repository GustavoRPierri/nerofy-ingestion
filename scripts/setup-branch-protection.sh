#!/bin/bash
# setup-branch-protection.sh
#
# Configura branch protection rules via GitHub API.
# Pré-requisitos:
#   - gh CLI instalado e autenticado
#   - PAT com permissão "repo" e "admin:repo_hook" configurado: gh auth login
#   - Variável GITHUB_REPOSITORY definida (ex: GustavoRPierri/nerofy-finance)
#
# Uso:
#   GITHUB_REPOSITORY=owner/repo ./scripts/setup-branch-protection.sh
#   ou simplesmente (se git remote estiver configurado):
#   ./scripts/setup-branch-protection.sh
#
set -e

REPO="${GITHUB_REPOSITORY:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"

echo "Configurando branch protection para: $REPO"
echo ""

# ── develop ───────────────────────────────────────────────────────────────────
# Requer: PR aprovado + checks de CI Feature (quality + unit tests)
echo "→ Configurando develop..."

gh api \
  --method PUT \
  "/repos/$REPO/branches/develop/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "CI Feature / Code Quality",
      "CI Feature / Unit Tests"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF

echo "  ✓ develop configurada"

# ── main ──────────────────────────────────────────────────────────────────────
# Requer: PR aprovado + integration tests (cobertura release/* e hotfix/*)
echo "→ Configurando main..."

gh api \
  --method PUT \
  "/repos/$REPO/branches/main/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "CI Integration / Integration Tests"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_linear_history": false
}
EOF

echo "  ✓ main configurada"

echo ""
echo "Branch protection configurada com sucesso!"
echo ""
echo "Resumo das regras:"
echo "  develop → requer PR + 1 aprovador + 'CI Feature / Code Quality' + 'CI Feature / Unit Tests'"
echo "  main    → requer PR + 1 aprovador + 'CI Integration / Integration Tests'"
echo ""
echo "IMPORTANTE: Adicione os seguintes secrets no repositório (Settings → Secrets → Actions):"
echo "  PAT_TOKEN  — Personal Access Token com permissão 'repo'"
echo "               (necessário para: criar PRs e branches via CI, configurar branch protection)"
