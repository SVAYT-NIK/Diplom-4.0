// BuildingSelector component
import React from 'react';
import type { Building } from '../services/types';

interface BuildingSelectorProps {
  buildings: Building[];
  selectedBuildingId: number | null;
  onSelectBuilding: (buildingId: number) => void;
  disabled?: boolean;
}

export const BuildingSelector: React.FC<BuildingSelectorProps> = ({
  buildings,
  selectedBuildingId,
  onSelectBuilding,
  disabled = false,
}) => {
  if (buildings.length === 0) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-yellow-800 text-sm">
          Нет доступных зданий. Загрузите данные Excel для начала работы.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        Выберите многоквартирный дом (МКД)
      </label>
      <select
        value={selectedBuildingId ?? ''}
        onChange={(e) => onSelectBuilding(Number(e.target.value))}
        disabled={disabled}
        className={`
          w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm 
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
          disabled:bg-gray-100 disabled:cursor-not-allowed
        `}
      >
        <option value="" disabled>
          -- Выберите здание --
        </option>
        {buildings.map((building) => (
          <option key={building.id} value={building.id}>
            {building.address} ({building.area_m2} м², {building.year_built} г.)
          </option>
        ))}
      </select>
      
      {selectedBuildingId && (
        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-gray-500">Площадь:</span>
              <span className="ml-2 font-medium">{buildings.find(b => b.id === selectedBuildingId)?.area_m2} м²</span>
            </div>
            <div>
              <span className="text-gray-500">Год постройки:</span>
              <span className="ml-2 font-medium">{buildings.find(b => b.id === selectedBuildingId)?.year_built}</span>
            </div>
            <div>
              <span className="text-gray-500">Тип отопления:</span>
              <span className="ml-2 font-medium">{buildings.find(b => b.id === selectedBuildingId)?.heating_type}</span>
            </div>
            <div>
              <span className="text-gray-500">Норматив:</span>
              <span className="ml-2 font-medium">{buildings.find(b => b.id === selectedBuildingId)?.norm_gcal_m2} Гкал/м²</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BuildingSelector;
