// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

import { describe, expect, it, vi } from 'vitest';
import ObjectList from './ObjectList.vue';

describe('ObjectList selection context', () => {
	it('exposes selected rows to list actions', () => {
		const selections = new Set(['two.example.com']);
		const state = {
			options: { context: {} },
			$list: {},
			selections,
			rows: [{ name: 'one.example.com' }, { name: 'two.example.com' }],
		};

		expect(ObjectList.computed.context.call(state).selectedRows).toEqual([
			{ name: 'two.example.com' },
		]);
	});

	it('retains and emits list selections', () => {
		const state = {
			selections: new Set(),
			$emit: vi.fn(),
		};
		const selections = new Set(['one.example.com']);

		ObjectList.methods.onSelectionChange.call(state, selections);

		expect([...state.selections]).toEqual(['one.example.com']);
		expect(state.$emit).toHaveBeenCalledWith('update:selections', selections);
	});
});
