// src/components/common/StepperBar.jsx
// Barre de progression multi-étapes numérotées avec libellés
import { Check } from 'lucide-react';

export default function StepperBar({ steps = [], currentStep = 1, totalSteps }) {
  const stepCount = totalSteps || steps.length;
  const safeProgress = stepCount > 1 ? ((currentStep - 1) / (stepCount - 1)) * 100 : 0;
  return (
    <div className="w-full">
      {/* Stepper horizontal */}
      <div className="flex items-center">
        {steps.map((step, index) => {
          const stepNumber = index + 1;
          const isCompleted = stepNumber < currentStep;
          const isCurrent = stepNumber === currentStep;
          const isLast = index === steps.length - 1;

          return (
            <div key={stepNumber} className="flex items-center flex-1 last:flex-none">
              {/* Cercle numéroté */}
              <div className="flex flex-col items-center">
                <div
                  className={`
                    w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold
                    transition-all duration-200
                    ${isCompleted
                      ? 'bg-success-500 text-white'
                      : isCurrent
                        ? 'bg-primary-700 text-white shadow-md'
                        : 'bg-gray-100 text-text-muted border border-border'
                    }
                  `}
                >
                  {isCompleted ? <Check size={16} /> : stepNumber}
                </div>
                {/* Label */}
                <span
                  className={`
                    text-[11px] font-medium mt-2 text-center whitespace-nowrap
                    ${isCurrent ? 'text-primary-700 font-semibold' : isCompleted ? 'text-success-600' : 'text-text-muted'}
                  `}
                >
                  {step.label}
                </span>
              </div>

              {/* Ligne de connexion */}
              {!isLast && (
                <div className="flex-1 mx-2 mt-[-20px]">
                  <div
                    className={`h-0.5 w-full transition-colors duration-200 ${
                      isCompleted ? 'bg-success-500' : 'bg-gray-200'
                    }`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Barre de progression linéaire */}
      <div className="mt-4 h-1 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-primary-500 rounded-full transition-all duration-300"
          style={{ width: `${Math.max(0, Math.min(100, safeProgress))}%` }}
        />
      </div>
    </div>
  );
}
