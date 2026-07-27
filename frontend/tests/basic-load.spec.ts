import { test, expect } from '@playwright/test';

test.describe('Basic Application Load', () => {
  test('should load the page and show empty state', async ({ page }) => {
    await page.goto('/');

    // Check title
    await expect(page).toHaveTitle(/Voice AI Agent/i);

    // Check header text
    await expect(page.locator('h1')).toHaveText('Voice AI Agent');

    // Check empty state text
    await expect(page.getByText('How can I help you?')).toBeVisible();
    await expect(page.getByText('Type a message or tap the microphone')).toBeVisible();

    // Check presence of UI components
    const input = page.getByTestId('chat-input');
    await expect(input).toBeVisible();
    await expect(input).toBeEnabled();

    const micButton = page.getByTestId('mic-button');
    await expect(micButton).toBeVisible();
    await expect(micButton).toBeEnabled();

    const sendButton = page.getByTestId('send-button');
    await expect(sendButton).toBeVisible();
    await expect(sendButton).toBeDisabled(); // Disabled initially because input is empty
  });

  test('should enable send button when typing', async ({ page }) => {
    await page.goto('/');

    const input = page.getByTestId('chat-input');
    const sendButton = page.getByTestId('send-button');

    await input.fill('Hello');
    await expect(sendButton).toBeEnabled();

    await input.fill('');
    await expect(sendButton).toBeDisabled();
  });
});
