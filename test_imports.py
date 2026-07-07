"""Quick import test — verifies all modules load without errors."""
import sys
print(f"Python {sys.version}")
print(f"CWD: {__import__('os').getcwd()}")
print()

try:
    import config
    print(f"[OK] config.py — CREATOR_NAME={config.CREATOR_NAME}")

    from mcp_server.main import mcp_server
    print(f"[OK] mcp_server — {len(mcp_server.list_tools())} tool(s) registered")

    result = mcp_server.call_tool("get_creator_metrics")
    try:
        subs = result["data"]["platforms"]["YouTube"]["subscribers"]
        print(f"[OK] MCP call — subscribers={subs}")
    except KeyError:
        print(f"[OK] MCP call — raw data: {result['data']}")

    from agents import triage_agent
    print("[OK] agents.triage_agent")

    from agents import negotiator_agent
    print("[OK] agents.negotiator_agent")

    from agents import creative_agent
    print("[OK] agents.creative_agent")

    from security import hitl_gatekeeper
    print("[OK] security.hitl_gatekeeper")

    import calendar_utils
    print("[OK] calendar_utils")

    # Test triage classification
    test_text = "From: test@brand.com\nSubject: Paid Collaboration\nBudget: $500\nWe want a partnership."
    result = triage_agent.classify(test_text)
    print(f"[OK] Triage test — classified as: {result['classification']} ({result['confidence']:.0%})")

    print()
    print("=" * 50)
    print("ALL IMPORTS AND BASIC TESTS PASSED")
    print("=" * 50)

except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
