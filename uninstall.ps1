<#
.SYNOPSIS
    .claude.json 에서 redmine MCP 항목을 제거.

.DESCRIPTION
    Windows 사용자용 wrapper. 내부적으로 redmine-mcp-uninstall (python -m redmine_mcp.installer:uninstall)을 호출.
    pip 패키지 자체도 제거하려면 추가로:
        pip uninstall redmine-mcp        # 또는: pipx uninstall redmine-mcp
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# redmine-mcp-uninstall이 PATH에 있으면 그걸로, 아니면 python -m 으로
& python -c "from redmine_mcp.installer import uninstall; import sys; sys.exit(uninstall())"
