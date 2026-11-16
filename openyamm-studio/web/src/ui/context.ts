// The store and the app's actions as React context: the app gives its own, the gallery one per panel state.
import { createContext, useContext } from 'react';
import { useStore } from 'zustand';
import type { StudioState, Store } from '../state/store.ts';
import { studio } from '../state/store.ts';
import type { Actions, Controller } from '../app/controller.ts';
import { quietActions } from '../app/controller.ts';

export interface StudioContextValue
{
    store: Store;
    actions: Actions;
    // Only the real app has one (the views register with it).
    controller?: Controller;
}

export const StudioContext = createContext<StudioContextValue>({ store: studio, actions: quietActions });

export function useStudioContext(): StudioContextValue
{
    return useContext(StudioContext);
}

export function useS<T>(select: (state: StudioState) => T): T
{
    return useStore(useContext(StudioContext).store, select);
}

export function useActions(): Actions
{
    return useContext(StudioContext).actions;
}
