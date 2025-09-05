from pydantic import BaseModel, Field
import itertools


_id_gen = itertools.count(1)


class MenuSchema(BaseModel):
    category: str
    dish: str
    dish_id: int = Field(default_factory=lambda: next(_id_gen))

    @property
    def split_dish_data(self):
        split_data = self.dish.split(" ")
        name = []
        price = "$X"
        description_data = []
        for element in split_data:
            if element.isupper() and "$" not in element:
                name.append(element)
            elif "$" in element:
                price = element
            else:
                description_data.append(element)
        dish_name = " ".join(name)
        description = " ".join(description_data)
        formatted_id = f"{self.dish_id:03d}"

        return {
            "category": self.category,
            "dish_name": dish_name,
            "price": price,
            "description": description,
            "dish_id": formatted_id,
        }
