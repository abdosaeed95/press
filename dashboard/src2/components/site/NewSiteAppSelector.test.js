// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest';
import NewSiteAppSelector from './NewSiteAppSelector.vue';

describe('New site app selector', () => {
	it('selects free apps and requests plans for paid apps', () => {
		const methods = NewSiteAppSelector.methods;
		const paidApp = {
			app: 'paid',
			subscription_type: 'Paid',
			plans: [{ name: 'paid-plan', price_inr: 100 }],
		};
		const context = {
			availableApps: [
				{ app: 'core', preinstalled: true },
				{ app: 'free' },
				paidApp,
			],
			apps: [{ app: 'core', preinstalled: true }],
			isAllSelected: false,
			pendingPlanApps: [],
			selectedApp: null,
			showAppPlanSelectorDialog: false,
			getAppName: methods.getAppName,
			requiresPlan: methods.requiresPlan,
			openNextPlanSelector() {
				methods.openNextPlanSelector.call(this);
			},
		};

		methods.toggleAllApps.call(context);

		expect(context.apps.map(methods.getAppName)).toEqual(['core', 'free']);
		expect(context.selectedApp).toBe(paidApp);
		expect(context.showAppPlanSelectorDialog).toBe(true);

		methods.selectAppPlan.call(context, paidApp.plans[0]);
		expect(context.apps.map(methods.getAppName)).toEqual([
			'core',
			'free',
			'paid',
		]);
		expect(context.apps.at(-1).plan.name).toBe('paid-plan');
	});

	it('keeps preinstalled apps when deselecting all', () => {
		const methods = NewSiteAppSelector.methods;
		const context = {
			availableApps: [{ app: 'core', preinstalled: true }, { app: 'free' }],
			apps: [{ app: 'core', preinstalled: true }, { app: 'free' }],
			isAllSelected: true,
			getAppName: methods.getAppName,
		};

		methods.toggleAllApps.call(context);

		expect(context.apps.map(methods.getAppName)).toEqual(['core']);
	});
});
