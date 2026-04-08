import { test, expect } from '@playwright/test';
import * as path from 'path';

test('ephysCT page loads and displays content', async ({ page }) => {
  // Navigate to the local ephysCT.html file
  const filePath = path.resolve(__dirname, '..', 'ephysCT.html');
  await page.goto(`file://${filePath}`);

  // Check that the page has loaded by verifying the title
  await expect(page).toHaveTitle(/primate/i);

  // Wait for any dynamic content to load
  await page.waitForLoadState('networkidle');

  // Verify that key elements are present
  await expect(page.locator('nav')).toBeVisible();
  await expect(page.locator('h2')).toContainText('Electrophysiology');
});
