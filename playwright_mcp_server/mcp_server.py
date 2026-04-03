"""
Playwright MCP Server - 基于FastMCP的浏览器自动化服务

提供浏览器控制功能：
- browser_close: 关闭浏览器
- browser_task_screenshot: 截取浏览器页面截图
- browser_fill_form: 填写表单字段
- browser_press_key: 模拟键盘按键
"""

import base64
from typing import Optional, List

from fastmcp import FastMCP
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# 创建FastMCP实例
mcp = FastMCP("playwright-mcp")

# 全局浏览器实例管理
_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None
_page: Optional[Page] = None
_playwright = None


async def get_or_create_page(url: Optional[str] = None) -> Page:
    """获取或创建浏览器页面，支持浏览器被关闭后自动重建"""
    global _browser, _context, _page, _playwright

    # 检查浏览器是否被关闭，如果是则重新创建
    if _browser is None or not _is_browser_connected(_browser):
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=False,
            channel='msedge'
        )
        _context = None
        _page = None

    # 检查 context 是否有效
    if _context is None or not _is_context_connected(_context):
        _context = await _browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        _page = None

    # 检查 page 是否有效
    if _page is None or not _is_page_connected(_page):
        _page = await _context.new_page()

    if url:
        await _page.goto(url)

    return _page


def _is_browser_connected(browser: Browser) -> bool:
    """检查浏览器是否仍然连接"""
    try:
        return browser.is_connected()
    except:
        return False


def _is_context_connected(context: BrowserContext) -> bool:
    """检查 context 是否仍然有效"""
    try:
        return context.pages is not None
    except:
        return False


def _is_page_connected(page: Page) -> bool:
    """检查页面是否仍然有效"""
    try:
        return not page.is_closed()
    except:
        return False


@mcp.tool()
async def browser_close() -> dict:
    """
    关闭浏览器实例
    
    Returns:
        dict: 包含关闭操作结果的字典
    """
    global _browser, _context, _page, _playwright

    result = {"success": True, "message": "浏览器已关闭"}

    try:
        if _page:
            try:
                await _page.close()
            except:
                pass
            _page = None

        if _context:
            try:
                await _context.close()
            except:
                pass
            _context = None

        if _browser:
            try:
                await _browser.close()
            except:
                pass
            _browser = None

        if _playwright:
            try:
                await _playwright.stop()
            except:
                pass
            _playwright = None

    except Exception as e:
        result = {"success": False, "message": f"关闭浏览器时出错: {str(e)}"}

    return result


@mcp.tool()
async def browser_task_screenshot(
        url: Optional[str] = None,
        selector: Optional[str] = None,
        full_page: bool = False,
        save_path: Optional[str] = None
) -> dict:
    """
    截取浏览器页面或元素的截图
    
    Args:
        url: 要访问的URL（可选，如果提供将导航到该URL）
        selector: CSS选择器（可选，截取特定元素）
        full_page: 是否截取整个页面（默认False，只截取视口）
        save_path: 保存截图的路径（可选）
    
    Returns:
        dict: 包含截图结果的字典，包含base64编码的图片数据或文件路径
    """
    global _page

    try:
        page = await get_or_create_page(url)

        # 等待页面加载
        if url:
            await page.wait_for_load_state("networkidle")

        result = {"success": True}

        if selector:
            # 截取特定元素
            element = page.locator(selector).first
            await element.wait_for(timeout=5000)

            if save_path:
                await element.screenshot(path=save_path)
                result["file_path"] = save_path
            else:
                screenshot_bytes = await element.screenshot()
                result["image_base64"] = base64.b64encode(screenshot_bytes).decode()
        else:
            # 截取整个页面或视口
            if save_path:
                await page.screenshot(path=save_path, full_page=full_page)
                result["file_path"] = save_path
            else:
                screenshot_bytes = await page.screenshot(full_page=full_page)
                result["image_base64"] = base64.b64encode(screenshot_bytes).decode()

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def browser_fill_form(
        url: Optional[str] = None,
        data: Optional[dict] = None,
        selector: Optional[str] = None,
        clear_first: bool = True
) -> dict:
    """
    填写表单字段
    
    Args:
        url: 要访问的URL（可选，如果提供将导航到该URL）
        data: 表单数据字典，格式为 {"selector": "value"}
        selector: 如果提供，仅填写匹配该选择器的表单
        clear_first: 填写前是否清空字段（默认True）
    
    Returns:
        dict: 包含填写操作结果的字典
    """
    try:
        page = await get_or_create_page(url)

        if url:
            await page.wait_for_load_state("networkidle")

        if not data:
            return {"success": False, "error": "未提供表单数据"}

        results = []

        for selector_pattern, value in data.items():
            try:
                locator = page.locator(selector_pattern)
                await locator.first.wait_for(timeout=5000)

                if clear_first:
                    await locator.first.clear()

                if isinstance(value, str):
                    await locator.first.fill(value)
                else:
                    await locator.first.fill(str(value))

                results.append({
                    "selector": selector_pattern,
                    "success": True,
                    "value": value
                })
            except Exception as e:
                results.append({
                    "selector": selector_pattern,
                    "success": False,
                    "error": str(e)
                })

        return {
            "success": all(r.get("success", False) for r in results),
            "results": results
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def browser_press_key(
        key: str,
        selector: Optional[str] = None,
        modifiers: Optional[List[str]] = None,
        count: int = 1
) -> dict:
    """
    模拟键盘按键
    
    Args:
        key: 按键名称（如 'Enter', 'Escape', 'Tab', 'a', 'A' 等）
        selector: CSS选择器（可选），如果提供，先点击该元素再按键
        modifiers: 修饰键列表（如 ['Control', 'Shift']）
        count: 按键次数（默认1）
    
    Returns:
        dict: 包含按键操作结果的字典
    """
    try:
        page = await get_or_create_page()

        # 如果提供了选择器，先点击该元素
        if selector:
            element = page.locator(selector).first
            await element.wait_for(timeout=5000)
            await element.click()

        # 构建按键参数
        keys_to_press = [key] * count

        # 执行按键
        await page.keyboard.press(key, count=count)

        return {
            "success": True,
            "key": key,
            "count": count,
            "modifiers": modifiers or []
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def browser_navigate(
        url: str,
        wait_until: str = "networkidle",
        timeout: int = 30000
) -> dict:
    """
    导航到指定URL
    
    Args:
        url: 目标URL
        wait_until: 等待加载状态，可选值: 'load', 'domcontentloaded', 'networkidle'
        timeout: 超时时间（毫秒）
    
    Returns:
        dict: 包含导航结果的字典
    """
    max_retries = 2

    for attempt in range(max_retries):
        try:
            page = await get_or_create_page(url)

            await page.goto(url, wait_until=wait_until, timeout=timeout)

            title = await page.title()

            return {
                "success": True,
                "url": page.url,
                "title": title
            }

        except Exception as e:
            error_msg = str(e)

            # 检查是否是浏览器被关闭导致的错误
            if "closed" in error_msg.lower() or "target" in error_msg.lower():
                # 重置全局状态并重试
                global _browser, _context, _page, _playwright
                _browser = None
                _context = None
                _page = None
                if attempt < max_retries - 1:
                    continue

            return {"success": False, "error": error_msg}

    return {"success": False, "error": "导航失败"}


@mcp.tool()
async def browser_click(
        selector: str,
        button: str = "left",
        click_count: int = 1,
        modifiers: Optional[List[str]] = None
) -> dict:
    """
    点击页面元素
    
    Args:
        selector: CSS选择器
        button: 鼠标按钮 ('left', 'right', 'middle')
        click_count: 点击次数（1=单击, 2=双击）
        modifiers: 修饰键列表
    
    Returns:
        dict: 包含点击操作结果的字典
    """
    try:
        page = await get_or_create_page()

        element = page.locator(selector).first
        await element.wait_for(timeout=5000)

        await element.click(
            button=button,
            click_count=click_count,
            modifiers=modifiers or []
        )

        return {
            "success": True,
            "selector": selector,
            "button": button,
            "click_count": click_count
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def browser_get_text(
        selector: str,
        url: Optional[str] = None
) -> dict:
    """
    获取页面元素的文本内容
    
    Args:
        selector: CSS选择器
        url: 可选的URL，导航到该页面后获取文本
    
    Returns:
        dict: 包含元素文本内容的字典
    """
    try:
        page = await get_or_create_page(url)

        if url:
            await page.wait_for_load_state("networkidle")

        element = page.locator(selector).first
        await element.wait_for(timeout=5000)

        text = await element.text_content()

        return {
            "success": True,
            "text": text,
            "selector": selector
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def browser_execute_script(
        script: str,
        url: Optional[str] = None
) -> dict:
    """
    在页面中执行JavaScript代码
    
    Args:
        script: 要执行的JavaScript代码
        url: 可选的URL，导航到该页面后执行脚本
    
    Returns:
        dict: 包含脚本执行结果的字典
    """
    try:
        page = await get_or_create_page(url)

        if url:
            await page.wait_for_load_state("networkidle")

        result = await page.evaluate(script)

        return {
            "success": True,
            "result": result
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def browser_status() -> dict:
    """
    获取浏览器状态信息
    
    Returns:
        dict: 包含浏览器当前状态的字典
    """
    global _browser, _context, _page

    status = {
        "browser_running": _browser is not None,
        "context_active": _context is not None,
        "page_active": _page is not None
    }

    if _page:
        try:
            status["current_url"] = _page.url
            status["title"] = await _page.title()
        except:
            pass

    return status
