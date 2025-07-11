import {create} from "zustand/react";

type FlowStoreType = {
    currentStep: number
    setCurrentStep: (step: number) => void
    increaseStep: () => void
}

const useFlowStore = create<FlowStoreType>((set, get) => ({
    currentStep: 0,
    setCurrentStep: step => set({currentStep: step}),
    increaseStep: () => set({currentStep: get().currentStep+1})
}))

export default useFlowStore;