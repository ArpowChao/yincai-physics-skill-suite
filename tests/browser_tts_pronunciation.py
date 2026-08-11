from __future__ import annotations

import argparse
import re
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--screenshot-dir", type=Path)
    args = parser.parse_args()

    console_errors: list[str] = []
    page_errors: list[str] = []
    requests: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error"
            else None,
        )
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on("request", lambda request: requests.append(request.url))
        page.goto(args.url)
        page.wait_for_load_state("networkidle")

        expect(page).to_have_title("配音稿校對台")
        expect(page.get_by_role("heading", name="讓文字正確，也讓聲音正確")).to_be_visible()
        expect(page.get_by_role("heading", name="先選一種方式開始")).to_be_visible()
        expect(page.locator(".input-choice")).to_have_count(2)
        choice_colors = page.locator(".input-choice").evaluate_all(
            "items => items.map(item => getComputedStyle(item).backgroundColor)"
        )
        assert len(set(choice_colors)) == 2, choice_colors
        page.get_by_role("button", name=re.compile("直接貼上文字")).click()
        assert page.evaluate("document.activeElement.id") == "sourceText"
        page.locator("#sourceText").fill(
            "他是這部電影的主角，也是一個重要角色。\n公式：x² + y² = z²"
        )
        expect(page.locator("#sourceText")).to_contain_text("主角")

        page.get_by_role("button", name="檢查這份文字").click()
        expect(page.locator(".review-card")).to_have_count(4)
        expect(page.locator('.review-card[data-type="reference"]')).to_have_count(1)
        expect(page.locator('.review-card[data-type="reference"]')).to_have_attribute(
            "data-status", "pending"
        )
        expect(page.locator("#speechText")).to_have_value(re.compile("主腳"))
        expect(page.locator("#speechText")).to_have_value(re.compile("x 的平方"))
        if not args.url.startswith("file:"):
            assert any(url.endswith("/data/verified.json") for url in requests), requests
        assert not any("/api/" in url for url in requests), requests

        first_card = page.locator(".review-card").first
        first_card.get_by_role("button", name="保留原稿").click()
        expect(page.locator("#speechText")).to_have_value(re.compile("主角"))

        page.locator("#ruleOriginal").fill("電影")
        page.locator("#ruleSpoken").fill("店影")
        page.evaluate(
            "submissionConfig.apps_script_url = ''; renderSubmissionProvider();"
        )
        page.evaluate("window.__openedGitHubUrl = ''; window.open = url => { window.__openedGitHubUrl = url; }")
        page.get_by_role("button", name="送交 GitHub 共用詞庫").click()
        github_url = page.evaluate("window.__openedGitHubUrl")
        assert "/issues/new" in github_url, github_url
        assert "%E9%9B%BB%E5%BD%B1" in github_url, github_url
        assert "%E5%BA%97%E5%BD%B1" in github_url, github_url

        page.evaluate(
            """
            submissionConfig.apps_script_url = 'https://script.google.com/macros/s/demo/exec';
            renderSubmissionProvider();
            window.__sheetSubmission = null;
            submitToAppsScript = function (endpoint, values) {
              window.__sheetSubmission = { action: endpoint, values };
            };
            void 0;
            """
        )
        page.get_by_role("button", name="送到 Google 共用候選表").click()
        sheet_submission = page.evaluate("window.__sheetSubmission")
        assert sheet_submission["action"].endswith("/demo/exec"), sheet_submission
        assert sheet_submission["values"]["original"] == "電影", sheet_submission
        assert sheet_submission["values"]["spoken"] == "店影", sheet_submission
        assert "電影" in sheet_submission["values"]["context"], sheet_submission

        page.get_by_role("button", name="只存這台裝置").click()
        expect(page.locator("#speechText")).to_have_value(re.compile("店影"))

        page.locator("#fileInput").set_input_files(
            {"name": "teacher.txt", "mimeType": "text/plain", "buffer": "角色".encode("utf-8")}
        )
        expect(page.locator("#speechText")).to_have_value("腳色")

        with page.expect_download() as download_info:
            page.get_by_role("button", name="下載配音稿").click()
        assert download_info.value.suggested_filename.endswith(".tts.txt")

        page.locator("#sourceText").fill("微小、儲存、頭髮、夾子、細菌、綜合。")
        page.get_by_role("button", name="檢查這份文字").click()
        expect(page.locator('.review-card[data-type="pronunciation"]')).to_have_count(6)
        expect(page.locator(".review-card__verified")).to_have_count(6)
        expect(page.locator("#speechText")).to_have_value(
            "圍小、廚存、頭法、頰子、細俊、縱合。"
        )

        page.locator("#sourceText").fill(
            "重力、測量、校正、數據、音樂、銀行、學校、處理。\n" * 25
        )
        page.get_by_role("button", name="檢查這份文字").click()
        assert page.locator(".review-card").count() >= 100
        assert page.locator(".review-card[open]").count() == 1
        list_geometry = page.locator("#reviewList").evaluate(
            "el => ({clientHeight: el.clientHeight, scrollHeight: el.scrollHeight})"
        )
        assert list_geometry["scrollHeight"] > list_geometry["clientHeight"], list_geometry
        assert list_geometry["clientHeight"] <= 700, list_geometry

        page.get_by_role("button", name="待確認", exact=True).click()
        page.get_by_role("button", name="待確認全部保留").click()
        expect(page.locator('.review-card[data-status="pending"]')).to_have_count(0)
        page.get_by_role("button", name="全部", exact=True).click()

        page.set_viewport_size({"width": 768, "height": 1000})
        rule_field_widths = page.locator(".rule-form > label").evaluate_all(
            "items => items.map(item => item.clientWidth)"
        )
        assert all(width >= 150 for width in rule_field_widths), rule_field_widths
        page_geometry = page.evaluate(
            "({clientWidth: document.documentElement.clientWidth, "
            "scrollWidth: document.documentElement.scrollWidth})"
        )
        assert page_geometry["scrollWidth"] <= page_geometry["clientWidth"], page_geometry
        summary_widths = page.locator(".review-card__compact").evaluate_all(
            "items => items.slice(0, 10).map(item => item.clientWidth)"
        )
        assert all(width >= 150 for width in summary_widths), summary_widths
        comparison_widths = page.locator(".pronunciation-comparison__item").evaluate_all(
            "items => items.slice(0, 10).map(item => item.clientWidth)"
        )
        assert all(width >= 120 for width in comparison_widths), comparison_widths
        page.set_viewport_size({"width": 1440, "height": 1000})

        if args.screenshot_dir:
            args.screenshot_dir.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(args.screenshot_dir / "tts-review-wide.png"),
                full_page=True,
            )
        browser.close()

    assert not console_errors, f"Console errors: {console_errors}"
    assert not page_errors, f"Page errors: {page_errors}"
    print("Browser flow passed: review, ignore, personal rule, and download.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
