from tkinter import Tk, StringVar, Label, Entry, Button, ttk
from tkinter.messagebox import showinfo, showerror
from models.vendas_dao import Vendas
from models.produtos_dao import Produtos
from datetime import datetime

class V_Window: 
    def only_numbers(self, char):
        return char.isdigit()
    
    def __init__(self):
        self.vendas = Vendas()
        self.produtos = Produtos()

        self.window = Tk()
        self.window.geometry('600x600')
        self.window.title('Registro de Vendas')
        self.window.resizable(False, False)

        self.id = StringVar()
        self.data = StringVar()
        self.produto_id = StringVar()
        self.quantidade = StringVar()
        self.total = StringVar()

        vcmd = (self.window.register(self.only_numbers), '%S')


        data_label = Label(self.window, text= 'Data da Venda:')
        data_label.pack(pady=10)

        data_entry = Entry(self.window, textvariable=self.data, width=15)
        data_entry.pack()

        produto_label = Label(self.window, text= 'ID do Produto:')
        produto_label.pack(pady=10)

        produto_entry = Entry(self.window, textvariable=self.produto_id, width=10, validate='key', validatecommand=vcmd)
        produto_entry.pack()

        quantidade_label = Label(self.window, text= 'Quantidade do Produto:')
        quantidade_label.pack(pady=10)

        quantidade_entry = Entry(self.window, textvariable=self.quantidade, width=10, validate='key', validatecommand=vcmd)
        quantidade_entry.pack()

        insert_button = Button(
            self.window, text='Inserir Venda', bg='green', fg= 'white',
            command=self.ao_clicar_inserir
        )
        insert_button.pack(pady=8)

        update_button = Button(
            self.window, text= 'Atualizar Venda', bg= '#FA5E09', fg= 'white',
            command=self.ao_clicar_atualizar
        )
        update_button.pack(pady=8)


        self.treeview = ttk.Treeview(self.window)
        self.treeview.bind('<Double-1>', self.populate_variables)

        table_label = Label(self.window, {'text': 'Tabela de Vendas'}) 
        table_label.pack()

        self.treeview['columns'] = ('ID', 'Data_Venda', 'Produto_Id', 'Quantidade', 'Total_Venda')
        self.treeview.column('#0', width=75, minwidth=15)
        self.treeview.column('ID', width=40, minwidth=5)
        self.treeview.column('Data_Venda', width=75, minwidth=10)
        self.treeview.column('Produto_Id', width=80, minwidth=5)
        self.treeview.column('Quantidade', width=80, minwidth=10)
        self.treeview.column('Total_Venda', width=100, minwidth=20)

        self.treeview.heading('#0', text='Label')
        self.treeview.heading('ID', text='ID')
        self.treeview.heading('Data_Venda', text='Data_Venda')
        self.treeview.heading('Produto_Id', text='Produto_Id')
        self.treeview.heading('Quantidade', text='Quantidade')
        self.treeview.heading('Total_Venda', text='Total_Venda')
        self.treeview.pack()

        delete_button = Button(
            self.window, text= 'Deletar Venda', bg= '#ED0000', fg= 'white',
            command=lambda: self.deletar_venda()
        )
        delete_button.pack(pady=8)

        refresh_button = Button(
            self.window, text= 'Carregar Tabela', bg= '#1634FA', fg= 'white',
            command=lambda: self.carregar_tabela()
        )
        refresh_button.pack(pady=8)

    def ao_clicar_inserir(self):
        data = self.data.get().strip()
        produto_id = self.produto_id.get().strip()
        quantidade = self.quantidade.get().strip()

        if data and produto_id and quantidade:
            print(f"[DEBUG] - Data: '{data}', Produto_ID: '{produto_id}', Quantidade: '{quantidade}'")

            self.inserir_venda(data, produto_id, quantidade)
        else:
            showerror('Erro', 'Preencha todos os campos antes de inserir.')
                      
    def inserir_venda(self, data: str, produto_id: str, quantidade: str) -> bool:
        try:
            produto_id = int(produto_id)
            quantidade = int(quantidade)
        except ValueError:
            showerror('Erro', 'Produto ID e Quantidade devem conter apenas números inteiros.')
            return False

        if not self.produto_disponivel(produto_id):
            return False

        if not self.validar_estoque(produto_id, quantidade):
            return False
        
        data = data.replace('/', '-')

        try:
            datetime.strptime(data, '%d-%m-%Y')
        except ValueError:
            showerror('Erro', 'Data inválida. Use o formato DD-MM-AAAA.')
            return False


        total_calculado = self.calcular_total_venda(produto_id, quantidade)
        if total_calculado == 0.0:
            return False
        
        self.total.set(str(total_calculado))

        if self.vendas.insert(data, produto_id, quantidade,total_calculado):
            print("Venda inserida com sucesso!")

            produto = self.produtos.select_by_id(produto_id)

            if not produto:
                showerror('Erro', 'Produto não encontrado.')
                return False
            
            try: 
                estoque_atual = int(produto[3])
                
                nova_quantidade = estoque_atual - quantidade
                
                if nova_quantidade < 0:
                    showerror('Erro', f'Estoque insuficiente.')
                    return False
                
            except (IndexError, ValueError):
                showerror('Erro', 'Erro ao acessar o estoque do produto.')
                return False
            
            self.produtos.atualizar_estoque(produto_id, nova_quantidade)

            self.limpar_campos()
            self.populate_table()

            return True
        else:
            showerror('Erro', 'Erro ao inserir a venda no banco de dados.')
            return False
    
    def ao_clicar_atualizar(self):
        id_venda = self.id.get().strip()
        data = self.data.get().strip()
        produto_id = self.produto_id.get().strip()
        quantidade = self.quantidade.get().strip()

        if id_venda and data and produto_id and quantidade:
            print(f"DEBUG - Atualizando ID: {id_venda}, Data: {data}, Produto_ID: {produto_id}, Quantidade: {quantidade}")
            self.atualizar_venda(id_venda, data, produto_id, quantidade)
        else:
            showerror('Erro', 'Preencha todos os campos antes de atualizar.')


    def atualizar_venda(self, id: str, data: str, produto_id: str, quantidade: str) -> bool:
        try:
            id = int(id)
            produto_id = int(produto_id)
            quantidade = int(quantidade)
        except ValueError:
            showerror('Erro', 'ID da venda, Produto ID e Quantidade devem conter apenas números inteiros.')
            return False
        
        if not self.produto_disponivel(produto_id):
            return False
        
        produto = self.produtos.select_by_id(produto_id)
        
        if not produto:
            showerror('Erro', 'Produto não encontrado.')
            return False

        try:
            quantidade_antiga = self.vendas.buscar_quantidade_por_id(id)
        
        except Exception as e:
            showerror('Erro', f'Erro ao buscar a venda anterior: {e}')
            return False
        

        data = data.replace('/', '-')
        total_calculado = self.calcular_total_venda(produto_id, quantidade)
        self.total.set(str(total_calculado))

        try:
            if self.vendas.update(id, data, produto_id, quantidade, total_calculado):
                print("Venda atualizada com sucesso!")

                estoque_atual = int(produto[3])

                if quantidade > quantidade_antiga:
                    nova_quantidade = estoque_atual - (quantidade - quantidade_antiga)
                else:
                    nova_quantidade = estoque_atual + (quantidade_antiga - quantidade)

                if nova_quantidade < 0:
                    showerror('Erro', f'Estoque insuficiente após a atualização. Estoque atual: {estoque_atual}')
                    return False
                
                self.produtos.atualizar_estoque(produto_id, nova_quantidade)

                self.limpar_campos()
                self.populate_table()
                return True
        except Exception as e:
            showerror('Erro', f'Ocorreu um erro inesperado ao atualizar a venda: {e}')
            return False


    def deletar_venda(self):
        table_data = self.treeview.selection()

        if len(table_data) > 0:
            showinfo('Dados Excluidos', 'A venda foi excluida com sucesso.')
            self.vendas.delete(int(table_data[0]))
            self.limpar_campos()
            self.populate_table()
        
        else:
            showerror('Erro', 'Não foi possível excluir os dados da venda.')

    def validar_estoque(self, id: int, quantidade: int) -> bool:
        try:
            qtd = int(quantidade)
        except ValueError:
            showerror("Erro", "Digite um número inteiro válido para a quantidade.")
            return False

        produto = self.produtos.select_by_id(id)

        if not produto:
            showerror('Erro', 'Produto não encontrado.')
            return False

        try:
            estoque_disponivel = int(produto[3])
        except (IndexError, ValueError):
            showerror("Erro", "Erro ao acessar a quantidade em estoque.")
            return False       

        if estoque_disponivel >= qtd:
            print(f'Estoque suficiente: {estoque_disponivel} disponível, {qtd} solicitado')
            return True           
        else:
            showerror('Erro', 'A quantidade do pedido não pode ser maior do que o estoque disponível.')
            return False

    def produto_disponivel(self, id: str) -> bool:
        try:
            id = int(id)
        except ValueError:
            showerror("Erro", "ID do produto inválido.")
            return False
        
        produto = self.produtos.select_by_id(id)
        print(f'produto_disponivel -> Produto retornado: {produto}')
        
        if produto:
            return True
        else:
            showerror('Produto Indisponível', 'Este produto não está mais disponivel.')
            return False
        
    def calcular_total_venda(self, id: str, quantidade: str) -> float:
        try:
            id_int = int(id)
            qtd = int(quantidade)
        except ValueError:
            showerror('Erro', 'Produto Id e Quantidade devem conter números válidos.')
            return 0.0

        produto = self.produtos.select_by_id(id_int)

        if not produto:
            showerror("Erro", "Produto não encontrado.")
            return 0.0
        
        try:
            preco = float(produto[2])
            total = preco * qtd
            total = round(total, 2)
            print(f'Preço Unitário: {preco}, Quantidade: {qtd}, Total: {total}')
            return total
        except (IndexError, ValueError):
            showerror('Erro', 'Erro ao calcular o total da venda.')
            return 0.0
        
    def limpar_campos(self):
        self.id.set('')
        self.data.set('')
        self.produto_id.set('')
        self.quantidade.set('')
        self.total.set('')

    def carregar_tabela(self):
        self.populate_table()

    def populate_variables(self, event=None):
        table_data = self.treeview.selection()
        if len(table_data) > 0: 
            venda = self.vendas.select_by_id(int(table_data[0]))

            if venda is not None:
                self.id.set(venda[0])
                self.data.set(venda[1])
                self.produto_id.set(venda[2])
                self.quantidade.set(venda[3])
                self.total.set(venda[4])
            else:
                showerror('Error', 'Não foi possível encontrar a venda.')

    def populate_table(self) -> None:
        self.clear_data()
        vendas = self.vendas.select_all()

        for venda in vendas:
            self.treeview.insert('', index='end', text='Venda', iid=str(venda[0]),
                                 values=(venda[0], venda[1], venda[2], venda[3], venda[4]))

    def clear_data(self) -> None:
        for item in self.treeview.get_children():
            self.treeview.delete(item)


    def run(self) -> None:
        self.window.mainloop() 


