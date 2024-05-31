import { Step, type StepItem, Stepper, useStepper } from "@/components/stepper";
import { Button } from "@/components/ui/button";

const steps = [
	{ label: "Step 1" },
	{ label: "Step 2" },
	{ label: "Step 3" },
] satisfies StepItem[];

export default function GenerationStepper() {
	return (
		<div className="flex w-full flex-col gap-4">
			<Stepper orientation="vertical" initialStep={0} steps={steps}>
				{steps.map((stepProps, index) => {
					return (
						<Step key={stepProps.label} {...stepProps}>
							<div className="h-40 flex items-center justify-center my-4 border bg-secondary text-primary rounded-md">
								<h1 className="text-xl">Step {index + 1}</h1>
							</div>
							<StepButtons />
						</Step>
					);
				})}
				<FinalStep />
			</Stepper>
		</div>
	);
}

const StepButtons = () => {
	const { nextStep, prevStep, isLastStep, isOptionalStep, isDisabledStep } =
		useStepper();
	return (
		<div className="w-full flex gap-2 mb-4">
			<Button
				disabled={isDisabledStep}
				onClick={prevStep}
				size="sm"
				variant="secondary"
			>
				Prev
			</Button>
			<Button size="sm" onClick={nextStep}>
				{isLastStep ? "Finish" : isOptionalStep ? "Skip" : "Next"}
			</Button>
		</div>
	);
};

const FinalStep = () => {
	const { hasCompletedAllSteps, resetSteps } = useStepper();

	if (!hasCompletedAllSteps) {
		return null;
	}

	return (
		<>
			<div className="h-40 flex items-center justify-center border bg-secondary text-primary rounded-md">
				<h1 className="text-xl">Woohoo! All steps completed! 🎉</h1>
			</div>
			<div className="w-full flex justify-end gap-2">
				<Button size="sm" onClick={resetSteps}>
					Reset
				</Button>
			</div>
		</>
	);
};
