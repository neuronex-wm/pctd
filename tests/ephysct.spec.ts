import { test, expect } from '@playwright/test';
import * as path from 'path';

test('ephysCT page loads and displays content', async ({ page }) => {
  // Navigate to the local ephysCT.html file
  const filePath = path.resolve(__dirname, '..', 'ephysCT.html');
  await page.goto(`file://${filePath}`);

  // Check that the page has loaded by verifying the title
  await expect(page).toHaveTitle(/ephys/i);

  // Wait for any dynamic content to load
  await page.waitForLoadState('networkidle');

  // Take an accessibility snapshot to view the page structure as AI would see it
  const snapshot = await page.accessibility.snapshot();
  
  // Log the snapshot for inspection
  console.log('Accessibility Snapshot:', JSON.stringify(snapshot, null, 2));

  // Verify that key interactive elements are present
  expect(snapshot).toBeTruthy();
});
